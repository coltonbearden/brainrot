# Surfaces — running brainrot outside the claude.ai app

The ten skills were designed around the claude.ai app's history and memory
tools. Everything they do also runs elsewhere; this file is the mapping. Each
skill's own `## Surfaces` section points here.

## Capability matrix

| Capability | claude.ai app | Claude Code | Anywhere with an export |
|---|---|---|---|
| History sweeps (`conversation_search`, `recent_chats`, `read_conversation`) | native | — | via export pass |
| Export ("deep") mode over `conversations.json` | native (upload) | native (local file) | native |
| Memory staging | `memory_user_edits` ledger (30-entry cap) | memory file, e.g. `~/.claude/CLAUDE.md` | memory file |
| File outputs | `/mnt/user-data/outputs/` + present-file | working directory | working directory |
| `/brainrot:arbitrate`, `/brainrot:runbook` commands | — (use the paste-in prompt) | native | — |

## History backend

**claude.ai app.** The past-chats tools are the native backend; every skill's
workflow uses them as written. Scope rule everywhere: chats inside a Project are
invisible from outside it, and vice versa.

**Everywhere else: the export pass.** Any skill whose preconditions name the
past-chats tools also runs against a conversations export. The sweep step
becomes a scripted regex pass over the export using that skill's own lexicon;
classification, thresholds, gates, evidence rules, and output format are
unchanged, and the per-call search budgets (20-chat pages, 5-call caps) don't
apply — coverage is `FULL (export)`.

Export sources, in order of preference:

1. **A claude.ai data export** — `conversations.json` from Settings → Privacy →
   Export data. This is your claude.ai history.
2. **Local Claude Code history** — run the bundled converter:

   ```bash
   python3 scripts/cc_history_export.py --days 30 --out conversations.json
   ```

   It reads `~/.claude/projects/**/*.jsonl` session transcripts and emits the
   same schema. Best-effort across Claude Code versions: unparseable records are
   counted and skipped, never guessed at.

Expected schema, which `friction-audit` and `claim-audit` already consume in
their deep modes:

```json
[ { "name": "...", "uuid": "...",
    "chat_messages": [ { "sender": "human", "text": "..." },
                       { "sender": "assistant", "text": "..." } ] } ]
```

The export contains your chat history. Keep it local; this repository's
`.gitignore` excludes `conversations*.json` so it is never committed by
accident.

## Memory backend

Rules and memory live in exactly one place per setup — pick it once and every
skill targets it:

- **claude.ai app:** the `memory_user_edits` ledger (30-entry cap) plus the
  in-context userMemories block. This is what the skills' staging steps assume.
- **Claude Code / other:** a memory file, default `~/.claude/CLAUDE.md`, with a
  clearly delimited rules section. Apply the same discipline the ledger enforces:
  a hard line cap (default 30) and a post-GC target (default 20) for the rules
  section, explicit before/after plans, explicit user confirmation before any
  edit, and a re-read verification after. `memory-gc`'s E0/E1 counts become line
  counts of that section; `rule-drift` extracts the rule set from it instead of
  the userMemories block.

The confirm gates are not optional on any backend: every skill here is read-only
until the user approves a written plan.

## Path mapping

| claude.ai path | elsewhere |
|---|---|
| `/mnt/user-data/uploads/<file>` | any path the user supplies |
| `/mnt/user-data/outputs/<file>` + present-file step | working directory (or a named path); skip presenting |
| `/mnt/skills` (skill-prospector dedupe) | `~/.claude/plugins/cache` + project `.claude/skills/` |

## Arbitration

The Phase 3 arbitration procedure is one document, `docs/arbitrate-prompt.md`,
with two front ends: the paste-in form for the claude.ai app and the
`/brainrot:arbitrate <cycle-dir>` command for Claude Code (inputs and outputs as
files). Both enforce the same interactive veto gate; neither writes memory.
