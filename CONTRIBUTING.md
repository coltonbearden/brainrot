# Contributing

Thanks for looking. This repo has a specific shape, and PRs that follow it get merged fast.

## Ground rules

Two properties are non-negotiable, because the whole toolkit reads private chat history:

1. **Read-only until confirmed.** No skill writes memory, files, or state without presenting an explicit before/after plan and receiving explicit approval. If your change adds a write path, it needs a gate.
2. **No network, no telemetry.** Nothing here phones home. Scripts touch local files only.

Beyond that: sensitive content is skipped and counted (`SKIPPED-SENSITIVE`), never quoted; assistant suggestions never become decisions or rules without human commitment.

## Setup

```bash
git clone https://github.com/coltonbearden/brainrot
cd brainrot
python3 plugins/brainrot/scripts/validate.py   # should exit 0
```

To test the plugin locally in Claude Code:

```
/plugin marketplace add /absolute/path/to/brainrot
/plugin install brainrot@brainrot
```

## Before you open a PR

```bash
claude plugin validate .                       # official schema
python3 plugins/brainrot/scripts/validate.py   # structural invariants
shellcheck scripts/*.sh plugins/brainrot/scripts/*.sh
```

All three run in CI. The structural validator enforces:

| Invariant | Rule |
|---|---|
| Frontmatter | exactly `name` + `description`, nothing else |
| `name` | kebab-case, identical to the directory name |
| `description` | ≤ 200 characters, and names its trigger phrases |
| Body | < 500 lines |

## Adding a skill

Skills here are built from a spec, not freehand — that's why `docs/build-prompts/` exists. Follow the pattern:

1. Write a build prompt in `docs/build-prompts/NN-<name>.md` covering: purpose, verbatim frontmatter, trigger phrases, embedded lexicon, workflow (imperative + numbered + gated), output template, guardrails, and validation gates.
2. Generate `plugins/brainrot/skills/<name>/SKILL.md` from it.
3. Keep the body section order used by every existing skill: **Purpose → Triggers → Preconditions → (lexicon/schema) → Workflow → Output template → Guardrails → Surfaces.**
4. Include a `## Surfaces` section. If the skill needs past-chats tools, say so in Preconditions and describe the export-pass fallback.
5. Add it to the table in `README.md` and to `CHANGELOG.md`.

A skill that proposes standing rules must also declare how its proposals enter arbitration — the record prefix (`CA-`, `AP-`, `FA-`, `PM-`, …) and how its evidence tiers map onto `STRONG` / `PROVENANCE-WEAK` / `PROPOSED`. See `plugins/brainrot/docs/arbitrate-prompt.md`.

## Changing arbitration

`plugins/brainrot/docs/arbitrate-prompt.md` is versioned and has a changelog at the bottom. Any change to gates, scoring, or the pool format bumps the version and gets a changelog entry. Both front ends — the paste-in prompt and `/brainrot:arbitrate` — must stay in sync, and both must keep the veto gate.

If you change scoring or gates, walk the change through `plugins/brainrot/fixtures/example-cycle/` and say in the PR what the output looked like before and after.

## Style

- Tables over prose in skill bodies. These are instructions for a model, not essays.
- Imperative, numbered, gated workflow steps. Every gate states its `EXPECT:`.
- Absolute paths in examples.
- No user-specific content — no personal project names, real memory contents, or private terms. The 1.0.0 release existed specifically to strip those; keep them out.

## Assets and the mascot

The mascot is original artwork for this project, drawn on a 16x15 pixel grid.
If you change it, change all four representations together so they stay in sync:
`assets/mascot.svg` (full), `assets/mascot-mark.svg` (small mark),
`assets/mascot.txt` (ASCII + palette), and the arrays in
`scripts/banner.sh`. `assets/banner.svg` embeds the same grid.

The palette is fixed: spore `#c5f24a`, live `#35d94f`, rot `#1e9c39`, deep rot
`#0d5a22`, void `#080b09`. Do not introduce art, names, or styling that implies
affiliation with or endorsement by Anthropic; the disclaimer in the README
footer and on the site stays.

The project site is `docs/index.html`, served by GitHub Pages from `docs/`.
It is a single self-contained file — edit it directly, keep it dependency-free,
and keep its copy consistent with `README.md`.

Site imagery is inline SVG or a data-URI, and the repo does not take `.png`
files — with exactly one documented exception. `docs/og-card.png` is the
1200×630 link-preview card behind the page's `og:image` and `twitter:image`;
it has to be a raster because crawlers will not render an SVG preview. Do not
edit it by hand and do not add a second `.png`. Regenerate it with:

```bash
python3 scripts/make_og_card.py
```

That script reads the pixel grid straight out of `assets/mascot-mark.svg` and
draws every character from a 5×7 bitmap font embedded in the script, so it
needs no image library, no SVG renderer, and no system font — standard library
only, and identical output on any machine. If you change the mascot, rerun it
and commit the new card. `check.sh` derives the filename from the `og:image`
tag and fails if the file is missing or is not 1200×630.

## Reporting bugs

Use the issue templates. For skill misbehavior, the useful report includes the surface (claude.ai app / Claude Code / export), the trigger phrase you used, what you expected, and what happened. **Paraphrase — never paste raw chat history or memory contents into a public issue.**
