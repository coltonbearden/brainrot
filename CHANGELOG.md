# Changelog

## Unreleased

- Project site: `docs/index.html`, a self-contained GitHub Pages page (zero
  script tags, inlined mascot SVGs, data-URI favicon), deployed by
  `.github/workflows/pages.yml`; pixel banner/mascot assets under `assets/`
  and a terminal banner at `scripts/banner.sh` (repo root).
- Governance: `CONTRIBUTING.md`, `SECURITY.md`, issue templates
  (skill misbehavior / repo bug / new skill), and a PR template.
- CI: `.github/workflows/validate.yml` — plugin structure, manifest JSON,
  export-script `py_compile`, shellcheck, banner smoke, claude.ai zip
  packaging, and referenced-path checks; README expanded to match.
- Fixes on top of the facelift: Pages deploys no longer cancel in-flight
  (`cancel-in-progress: false`); site honors `prefers-reduced-motion` and
  drops contradictory/duplicate mascot ARIA labels; Open Graph + Twitter
  card metadata added; repo scaffolding (`CLAUDE.md`, `.claude/settings.json`,
  gitignore entry for `.claude/settings.local.json`); doc path corrections
  in README / SECURITY / CONTRIBUTING.
- Validation suite committed as `scripts/check.sh` (eight sections, one
  command); CI's shell and docs jobs folded into it.

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
