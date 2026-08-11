# brainrot

A self-audit toolkit for Claude. Ten skills that mine **your own chat history**
for corrections, ambiguity, drift, and wins; an arbitration pipeline that
distills the findings into a small, evidence-gated rule set; and a garbage
collector that keeps persistent memory lean. The premise: your history already
contains the record of what Claude gets wrong for you and what it nails — this
plugin turns that record into a maintained, budgeted set of standing rules
instead of an ever-growing pile of vibes.

Everything is read-only by default. Every memory write sits behind an explicit
per-plan confirmation gate.

## What's inside

One plugin, `brainrot`, containing ten skills and two commands:

| Skill | What it does |
|---|---|
| `memory-gc` | Audit + consolidate persistent memory; verify volatile claims against history; single gated write |
| `rule-drift` | Score adherence to your standing rules; verdict each KEEP / REINFORCE / REWRITE / RETIRE |
| `claim-audit` | Find facts Claude asserted that you corrected; root-cause; draft prevention rules |
| `ambiguity-preempt` | Find clarify-loops and wrong guesses; draft standing disambiguation defaults |
| `friction-audit` | Mine frustration/correction patterns; rank; one remediation per pattern |
| `praise-miner` | Find praised zero-correction outputs; extract the antecedents; draft do-more rules |
| `decision-ledger` | Harvest real decisions (human commitments only) into one dated, conflict-checked ledger |
| `usage-retro` | Sampled 7/30-day retrospective: correction rate, delegation ratio, trends |
| `skill-prospector` | Find recurring task shapes worth packaging as skills; scored backlog |
| `handoff-distill` | Distill a session into a canonical handoff block with provenance gates |

| Command | What it does |
|---|---|
| `/brainrot:runbook [cycle-dir]` | Where you are in a cleanup cycle and the exact next step |
| `/brainrot:arbitrate <cycle-dir>` | Phase 3: arbitrate all proposed rules into a budget-fitted selection (interactive veto gate) |

Five of the skills propose rules; the arbitration step exists so they compete
for scarce memory lines on evidence instead of landing by default. The full
sequence — baseline, audit, mine, arbitrate, single write, prospect — is in
[`plugins/brainrot/docs/runbook.md`](plugins/brainrot/docs/runbook.md).

## Install

**Claude Code** (plugin, recommended):

```
/plugin marketplace add coltonbearden/brainrot
/plugin install brainrot@brainrot
```

Skills are namespaced (`/brainrot:memory-gc`, …) and also trigger on their
natural phrases ("run memory gc", "what annoys me", "run praise miner").

**claude.ai app** (per-skill upload): the history-mining skills were designed
around the claude.ai app's past-chats and memory tools, so this surface gets the
richest behavior. Package each skill as an uploadable zip:

```bash
bash plugins/brainrot/scripts/package_claude_ai_zips.sh   # -> dist/<skill>.zip
```

then upload the ones you want via Settings → Capabilities → Skills. For Phase 3
on this surface, use the paste-in prompt in
[`plugins/brainrot/docs/arbitrate-prompt.md`](plugins/brainrot/docs/arbitrate-prompt.md).

## Surface support

| Capability | claude.ai app | Claude Code |
|---|---|---|
| History sweeps via past-chats tools | ✅ native | via export |
| Export ("deep") mode | ✅ upload `conversations.json` | ✅ `scripts/cc_history_export.py` bridges local `~/.claude/projects` history |
| Memory staging (gated) | ✅ `memory_user_edits` ledger | ✅ memory file, e.g. `~/.claude/CLAUDE.md` |
| `/brainrot:*` commands | — (paste-in prompt) | ✅ |

Details, schemas, and the exact tool/path/backend mapping:
[`plugins/brainrot/docs/surfaces.md`](plugins/brainrot/docs/surfaces.md).

## Safety and privacy

- **Read-only by default.** Every skill reports before it touches anything;
  memory edits happen only after you approve an explicit before/after plan, and
  are re-verified after execution.
- **Your history stays yours.** Sweeps run inside your own account or on your
  own machine. Exports (`conversations*.json`) are gitignored so they can't be
  committed by accident.
- **Sensitive content is skipped, counted, never quoted.** Every mining skill
  carries a `SKIPPED-SENSITIVE` convention.
- **Provenance gates.** An assistant suggestion never becomes a "decision" or a
  standing rule without an explicit human commitment; praise is evidence about
  what to repeat, never a record of a decision. Unverifiable claims go to you
  for a ruling instead of being silently rewritten.
- **Budget honesty.** Arbitration fits rules to real headroom and says so when
  there is none, rather than smuggling rules past the cap.

## Repository layout

```
.claude-plugin/marketplace.json      marketplace catalog
plugins/brainrot/                    the plugin
  .claude-plugin/plugin.json
  commands/                          runbook, arbitrate
  skills/<name>/SKILL.md             the ten skills
  docs/                              runbook, surfaces, arbitrate-prompt (v2.1)
  scripts/                           cc_history_export.py, validate.py, package_claude_ai_zips.sh
  fixtures/example-cycle/            worked arbitration input for testing
docs/build-prompts/                  provenance: the prompts each skill was built from
```

`docs/build-prompts/` is the toolkit's provenance: one standalone build prompt
per skill, usable as templates for building your own.

## Validate

```bash
claude plugin validate .                       # official schema check
python3 plugins/brainrot/scripts/validate.py   # structural + frontmatter invariants
```

## License

MIT — see [LICENSE](LICENSE).
