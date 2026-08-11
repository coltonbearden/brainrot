## What this changes

<!-- One paragraph. Link the issue if there is one. -->

## Checks

```
claude plugin validate .
python3 plugins/brainrot/scripts/validate.py
shellcheck scripts/*.sh
shellcheck plugins/brainrot/scripts/*.sh
```

- [ ] All of the above pass locally
- [ ] No user-specific content — no personal project names, real memory contents, or private terms
- [ ] No new network calls, telemetry, or update checks

## If this touches a skill

- [ ] Frontmatter is exactly `name` + `description`; `name` matches the directory and is kebab-case
- [ ] `description` is under 200 characters and names its trigger phrases
- [ ] Body follows the standard order: Purpose -> Triggers -> Preconditions -> (lexicon/schema) -> Workflow -> Output template -> Guardrails -> Surfaces
- [ ] Body is under 500 lines
- [ ] Every gate states its `EXPECT:`
- [ ] `README.md` table and `CHANGELOG.md` updated

## If this adds or changes a write path

- [ ] It presents an explicit before/after plan and requires approval
- [ ] It re-verifies what actually landed after execution

## If this touches arbitration

- [ ] `docs/arbitrate-prompt.md` version bumped and changelog entry added
- [ ] The paste-in prompt and `/brainrot:arbitrate` are still in sync, both keeping the veto gate
- [ ] Walked through `plugins/brainrot/fixtures/example-cycle/` — before/after output described below

<!-- before / after fixture output -->

## If this touches the mascot or site

- [ ] `mascot.svg`, `mascot-mark.svg`, `mascot.txt`, `banner.svg` and `banner.sh` are all in sync
- [ ] Palette unchanged; nothing implies Anthropic affiliation; disclaimer intact
