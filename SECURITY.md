# Security & privacy

`brainrot` reads private conversation history. That makes its threat model mostly
about **data handling**, not remote exploitation.

## What this software does and does not do

| | |
|---|---|
| Network calls | **None.** No telemetry, analytics, update checks, or external services |
| Data leaving your machine | **None.** Skills are Markdown instructions; scripts touch local files only |
| Writes | Gated. Every skill is read-only until you approve an explicit before/after plan |
| History exports | Written to your working directory. `.gitignore` excludes `conversations*.json` and `*-export.json` |
| Sensitive content | Skipped and counted (`SKIPPED-SENSITIVE`), never quoted or summarized into rules |

## Handling your own exports

`scripts/cc_history_export.py` produces a `conversations.json` containing your
chat history in plaintext. Treat it like a password vault export:

- Keep it local; do not commit it, upload it to a shared drive, or attach it to an issue.
- Delete it when the audit is done.
- If you must share a run for debugging, paraphrase. Never paste raw history or memory contents into a public issue or PR.

## Reporting a vulnerability

Open a [private security advisory](https://github.com/coltonbearden/brainrot/security/advisories/new)
rather than a public issue. Please include the affected file, the surface it
reproduces on, and the impact.

Things worth reporting: a skill that writes without hitting its confirmation
gate; a path that could exfiltrate history; a guardrail that can be bypassed by
crafted conversation content; a script that writes outside its documented
target.

Expect an initial response within 7 days.

## Supported versions

The latest release on `main` is supported. See [CHANGELOG.md](CHANGELOG.md).
