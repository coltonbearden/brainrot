# Changelog

## 1.0.0 — 2026-08-11

Initial public release.

- Ten history-audit skills packaged as one Claude Code plugin, normalized from a
  personal suite: all user-specific rules, project names, memory-state numbers,
  and exclusion terms removed or parameterized.
- Arbitration pipeline v2.1: adds the `praise-miner` proposal pool (`PM-` records,
  `C` fixed at 1 for do-more rules), replaces the hardcoded exclusion rule with a
  parameterized permanent-exclusion list (`R-EXCLUDED`), and ships in two forms —
  a `/brainrot:arbitrate` command (file mode) and a paste-in prompt
  (`docs/arbitrate-prompt.md`) for the claude.ai app.
- Cross-surface support: `scripts/cc_history_export.py` bridges local Claude Code
  history into the skills' export ("deep") mode; per-skill Surfaces sections map
  tools, memory backends, and paths per environment.
- Structural validator (`scripts/validate.py`), claude.ai per-skill zip packaging
  (`scripts/package_claude_ai_zips.sh`), example fixture cycle for testing
  `/brainrot:arbitrate`, and build-prompt provenance under `docs/build-prompts/`.
