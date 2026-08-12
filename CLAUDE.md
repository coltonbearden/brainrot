# brainrot

A Claude Code **plugin marketplace** whose single plugin ships **ten self-audit skills**
plus two commands (`/brainrot:runbook`, `/brainrot:arbitrate` — implemented as
command-style skills since the plugin `commands/` directory went legacy). The skills mine the user's own Claude chat history for corrections,
ambiguity, drift and wins, arbitrate the findings against a scarce memory budget, and
land the survivors in one gated write.

Public repo: `coltonbearden/brainrot` · MIT · site at https://coltonbearden.github.io/brainrot/

## Layout

```
.claude-plugin/marketplace.json   marketplace catalog (root manifest)
plugins/brainrot/
  .claude-plugin/plugin.json      plugin manifest
  skills/<name>/SKILL.md          the ten audit skills, plus the runbook and
                                  arbitrate command-style skills
  docs/                           runbook.md, surfaces.md, arbitrate-prompt.md
  scripts/                        cc_history_export.py, validate.py,
                                  package_claude_ai_zips.sh
  fixtures/example-cycle/         worked input for a full dry run
docs/build-prompts/               one build prompt per skill (provenance)
docs/index.html                   the GitHub Pages site
docs/og-card.png                  og:image link-preview card (the one .png)
scripts/banner.sh                 terminal banner (repo root, NOT under plugins/)
scripts/check.sh                  the check suite (runs every command below)
scripts/make_og_card.py           regenerates docs/og-card.png (stdlib only)
assets/                           banner.svg, mascot.svg, mascot-mark.svg, mascot.txt
```

`banner.sh` lives at the repo root. It was moved out of `plugins/brainrot/scripts/`
during the v2 facelift — if you find a reference to `plugins/brainrot/scripts/banner.sh`
anywhere, it is stale and should be fixed.

## Commands

```bash
bash scripts/check.sh                             # the one-liner: runs everything below
claude plugin validate .                          # marketplace manifest
claude plugin validate ./plugins/brainrot         # plugin manifest
python3 plugins/brainrot/scripts/validate.py      # structural invariants -> "OK"
shellcheck scripts/*.sh plugins/brainrot/scripts/*.sh
./scripts/banner.sh                               # also --small, and NO_COLOR=1 --plain
python3 scripts/make_og_card.py                   # -> docs/og-card.png, 1200x630
bash plugins/brainrot/scripts/package_claude_ai_zips.sh   # -> dist/, exactly 10 zips
rm -rf dist                                       # always clean up after packaging
```

All of the above run in CI (`.github/workflows/validate.yml`, jobs: validate / check).
Run them locally before opening a PR. `docs/**` changes additionally fire
`.github/workflows/pages.yml`.

## Structural invariants (enforced by validate.py — do not break)

| Invariant | Rule |
|---|---|
| Frontmatter | must have `name` + `description`; may also have only `disable-model-invocation`, `allowed-tools`, `argument-hint` |
| `name` | kebab-case, identical to the containing directory name |
| `description` | ≤ 200 characters, and (for the audit skills) names its trigger phrases |
| Body | < 500 lines |

Every **audit** skill body keeps this section order:
**Purpose → Triggers → Preconditions → (lexicon/schema) → Workflow → Output template →
Guardrails → Surfaces.**
The two command-style skills (`runbook`, `arbitrate`) are procedural bodies and are
exempt from that section order; `arbitrate` carries `disable-model-invocation: true`
so it only ever fires on explicit `/brainrot:arbitrate` invocation. They are also
deliberately excluded from claude.ai zip packaging (`COMMAND_SKILLS` in
`package_claude_ai_zips.sh`, mirrored in `check.sh`) — the claude.ai surface for
arbitration is the paste-in prompt.

## Safety posture (non-negotiable — this is the product)

These are promises the README and the site make to users. Do not weaken them:

1. **Read-only until confirmed.** No skill writes memory, files, or state without
   presenting an explicit before/after plan and receiving explicit approval.
   A new write path needs a gate.
2. **No network, no telemetry.** Nothing phones home. Scripts touch local files only.
3. **Sensitive content is skipped and counted** (`SKIPPED-SENSITIVE`), never quoted.
   Health, grief and crisis content is not surfaced, summarized, or turned into a rule.
4. **Provenance gates.** An assistant *suggestion* never becomes a "decision" or a
   standing rule without an explicit human commitment.
5. **Budget honesty.** Arbitration fits rules to real headroom and says when there is
   none, rather than smuggling rules past the cap.

## Never commit

- Chat-history exports: `conversations*.json`, `*-export.json` (gitignored)
- `RESULTS.md` (gitignored; local verification log, contains a personal email)
- `dist/` (gitignored packaging output)
- Anything from `~/projects/brainrot-design-handoff/` — that bundle's `uploads/`
  directory holds **third-party copyrighted reference images** that must never enter
  this repo under any path. Also excluded from it: `*.dc.html`, `support.js`,
  `.thumbnail`, `github.md`.
- Any `.png` **except `docs/og-card.png`** — the link-preview card, and the sole
  documented exception (issue #14). Regenerate it with
  `python3 scripts/make_og_card.py`; never add a second one. All other site
  imagery stays inline SVG or a data-URI.

## The site (`docs/index.html`)

One self-contained static file. Constraints:

- **Zero `<script>` tags.** Interactivity is CSS-only (`<details>/<summary>`).
- Both mascot SVGs are **inlined**; the favicon is a data-URI of `mascot-mark.svg`.
  GitHub Pages serves only `docs/`, so no relative asset path may point outside it.
- Google Fonts: Silkscreen + JetBrains Mono. Preserve `image-rendering: pixelated`,
  the palette, and the `bob` keyframe.
- Every `href="#..."` must have a matching `id` in the file.
- Keep it under 120KB.
- `docs/og-card.png` is the one asset the page references instead of inlining —
  crawlers will not render an SVG link preview. `og:image` and `twitter:image`
  carry its **absolute** URL and `twitter:card` is `summary_large_image`;
  `check.sh` derives the filename from the `og:image` tag and fails if the file
  is missing or is not 1200×630.

Note: `pages.yml` uploads all of `docs/`, so `docs/build-prompts/*.md` is published
too. That is currently accepted, not accidental-but-unnoticed.

## Adding a skill

Skills are built from a spec, not freehand:

1. Write `docs/build-prompts/NN-<name>.md` covering purpose, verbatim frontmatter,
   trigger phrases, embedded lexicon, workflow (imperative + numbered + gated),
   output template, guardrails, and validation gates.
2. Generate `plugins/brainrot/skills/<name>/SKILL.md` from it.
3. Include a `## Surfaces` section. If it needs past-chats tools, say so in
   Preconditions and describe the export-pass fallback.
4. Add it to the table in `README.md` and to `CHANGELOG.md`.
5. A skill that proposes standing rules must declare how its proposals enter
   arbitration: its record prefix (`CA-`, `AP-`, `FA-`, `PM-`, …) and how its evidence
   tiers map onto `STRONG` / `PROVENANCE-WEAK` / `PROPOSED`.
   See `plugins/brainrot/docs/arbitrate-prompt.md`.

Changing arbitration bumps the version in `docs/arbitrate-prompt.md` and adds a
changelog entry there. Both front ends — the paste-in prompt and `/brainrot:arbitrate` —
must stay in sync, and both must keep the veto gate.

## Working conventions

- **Give absolute paths in commands.** Never "the repo" or "that folder."
- **Reproduce full corrected files after an edit**, not fragments.
- **Search before asserting** versions, prices, or current product status.
- Release history is load-bearing: tag `v1.0.0` at `7b5aedc`, its GitHub release, and
  issues #1–3 are not to be modified. Never force-push, hard-reset, or delete tags.
- Session reports and build prompts live **outside** the repo in `~/projects/` on
  purpose. Keep new ones there; they are provenance, not repo content.
- Completed passes' reports and prompts move to `~/projects/brainrot-archive/<pass>/`;
  the in-flight pass's files stay loose in `~/projects/` until the next pass consumes them.
