#!/usr/bin/env python3
"""Export local Claude Code session history to a conversations.json-style file.

Bridges Claude Code environments into the brainrot skills' export ("deep") mode.
Output schema (what the skills expect):

    [ { "name": str, "uuid": str,
        "chat_messages": [ { "sender": "human"|"assistant", "text": str } ] } ]

Best-effort across Claude Code versions: unknown JSONL records are skipped and
counted, never guessed at. The export contains your chat history — keep it
local and out of version control (this repo's .gitignore already excludes
conversations*.json).

Usage:
    python3 cc_history_export.py [--source ~/.claude/projects] [--out conversations.json]
                                 [--days 30] [--project SUBSTRING]
"""
import argparse, json, sys, time
from pathlib import Path


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [p.get("text", "") for p in content
                 if isinstance(p, dict) and p.get("type") == "text"]
        return "\n".join(t for t in parts if t)
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--out", default="conversations.json")
    ap.add_argument("--days", type=int, default=None,
                    help="only include session files modified in the last N days")
    ap.add_argument("--project", default=None,
                    help="only include session files whose path contains this substring")
    a = ap.parse_args()

    src = Path(a.source).expanduser()
    if not src.is_dir():
        sys.exit(f"source not found: {src}")
    cutoff = time.time() - a.days * 86400 if a.days else None

    convs, skipped_lines, files_seen = [], 0, 0
    for f in sorted(src.rglob("*.jsonl")):
        if a.project and a.project not in str(f):
            continue
        if cutoff and f.stat().st_mtime < cutoff:
            continue
        files_seen += 1
        msgs, session_id = [], None
        for line in f.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped_lines += 1
                continue
            if not isinstance(obj, dict):
                skipped_lines += 1
                continue
            session_id = session_id or obj.get("sessionId")
            if obj.get("type") not in ("user", "assistant"):
                continue
            msg = obj.get("message") or {}
            text = text_of(msg.get("content"))
            if not text.strip():
                continue  # tool results / non-text turns
            msgs.append({"sender": "human" if obj["type"] == "user" else "assistant",
                         "text": text})
        if not msgs:
            continue
        first_human = next((m["text"] for m in msgs if m["sender"] == "human"), f.stem)
        convs.append({"name": first_human.strip().replace("\n", " ")[:80] or f.stem,
                      "uuid": session_id or f.stem,
                      "chat_messages": msgs})

    Path(a.out).write_text(json.dumps(convs, indent=1))
    print(f"{len(convs)} conversations from {files_seen} session files -> {a.out}"
          f" ({skipped_lines} unparseable lines skipped)")
    if not convs:
        print("warning: empty export — check --source/--days/--project", file=sys.stderr)


if __name__ == "__main__":
    main()
