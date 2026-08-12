#!/usr/bin/env python3
"""Structural validator for this marketplace. Run from anywhere; exits nonzero on failure.

Checks: marketplace.json and plugin.json shape, plugin sources exist, every
SKILL.md frontmatter has name+description (plus, optionally, only
disable-model-invocation / allowed-tools / argument-hint), name == dir and
kebab-case, description <= 200 chars, body < 500 lines.
Complements `claude plugin validate .`, which checks the official schema.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
errs = []


def err(m):
    errs.append(m)


def frontmatter(path):
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines
    fm, i = {}, 1
    while i < len(lines) and lines[i].strip() != "---":
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", lines[i])
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
        i += 1
    return (fm, lines) if i < len(lines) else (None, lines)


mkt_path = ROOT / ".claude-plugin/marketplace.json"
try:
    mkt = json.loads(mkt_path.read_text())
    for field in ("name", "owner", "plugins"):
        if field not in mkt:
            err(f"marketplace.json missing {field}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", mkt.get("name", "")):
        err("marketplace name must be kebab-case")
    for entry in mkt.get("plugins", []):
        src = entry.get("source")
        if isinstance(src, str):
            if not src.startswith("./"):
                err(f"{entry.get('name')}: relative source must start with ./")
            elif not (ROOT / src).is_dir():
                err(f"{entry.get('name')}: source dir missing: {src}")
except Exception as e:
    err(f"marketplace.json: {e}")

for pdir in sorted((ROOT / "plugins").iterdir()):
    if not pdir.is_dir():
        continue
    try:
        pj = json.loads((pdir / ".claude-plugin/plugin.json").read_text())
        for field in ("name", "version", "description", "author"):
            if field not in pj:
                err(f"{pdir.name}/plugin.json missing {field}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pj.get("name", "")):
            err(f"{pdir.name}: plugin name must be kebab-case")
    except Exception as e:
        err(f"{pdir.name}/plugin.json: {e}")

    for sk in sorted((pdir / "skills").glob("*/SKILL.md")):
        fm, lines = frontmatter(sk)
        rel = sk.relative_to(ROOT)
        if fm is None:
            err(f"{rel}: unreadable frontmatter")
            continue
        missing = {"name", "description"} - set(fm)
        extra = set(fm) - {"name", "description", "disable-model-invocation", "allowed-tools", "argument-hint"}
        if missing:
            err(f"{rel}: frontmatter missing {sorted(missing)}")
        if extra:
            err(f"{rel}: unexpected frontmatter keys {sorted(extra)}")
        if fm.get("name") != sk.parent.name:
            err(f"{rel}: name != directory")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", fm.get("name", "")):
            err(f"{rel}: name must be kebab-case")
        if len(fm.get("description", "")) > 200:
            err(f"{rel}: description > 200 chars")
        if len(lines) >= 500:
            err(f"{rel}: {len(lines)} lines (cap 500)")

if errs:
    print("FAIL")
    for e in errs:
        print(" -", e)
    sys.exit(1)
print(f"OK — validated {ROOT}")
