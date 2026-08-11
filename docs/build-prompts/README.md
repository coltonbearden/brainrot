# claude.ai Skill Build Prompts — v1.0 (2026-08-10)

Ten standalone build prompts. One file = one fresh claude.ai chat session = one uploadable skill zip.

## Usage
1. Open a **new chat outside any Project** on claude.ai (code execution + file creation ON).
2. Paste the **entire contents of one numbered file** as the first message. No other context needed.
3. The session delivers `/mnt/user-data/outputs/<skill>.zip` → download → Settings → Capabilities → Skills → Upload skill.
4. Repeat per file. Numbering = recommended build order.

## Index
| # | File | Skill | Function | Writes memory? | Writes files? |
|---|------|-------|----------|----------------|---------------|
| 01 | 01-memory-gc.md | memory-gc | Audit + consolidate persistent memory | Yes (gated) | No |
| 02 | 02-friction-audit.md | friction-audit | Mine frustration/correction patterns | Optional (gated) | No |
| 03 | 03-skill-prospector.md | skill-prospector | Recurring tasks → scored skill backlog | No | No |
| 04 | 04-handoff-distill.md | handoff-distill | Canonical session handoff block | No | Optional |
| 05 | 05-claim-audit.md | claim-audit | Hallucination incident log + prevention rules | Optional (gated) | No |
| 06 | 06-ambiguity-preempt.md | ambiguity-preempt | Clarify-loops → standing disambiguation rules | Optional (gated) | No |
| 07 | 07-praise-miner.md | praise-miner | Success antecedents → do-more rules | Optional (gated) | No |
| 08 | 08-rule-drift.md | rule-drift | Standing-rule adherence audit | Optional (gated) | No |
| 09 | 09-decision-ledger.md | decision-ledger | Harvest decisions → DECISIONS-GLOBAL.md | No | Yes |
| 10 | 10-usage-retro.md | usage-retro | Sampled 7/30d metrics retrospective | No | Yes |

## Build order rationale
01 pays out on every future turn; 02 generates the evidence feed 05/06/08 reuse; 03 feeds the skill backlog; 04 is daily-use. 10 last — it consumes the others' outputs.

## Merge option
02 / 05 / 07 share one sweep core. To consolidate later: fresh session, attach those three prompt files, say "merge into one skill named interaction-audit with three lexicon modes; same gates."

## Invariants baked into every prompt
- claude.ai upload limits (validated): name lowercase = directory, description ≤200 chars, SKILL.md <500 lines, frontmatter = name + description only.
- Verification gates with expected values at every build step.
- Destructive memory ops always behind an explicit user-confirm gate.
- No placeholders; zero clarifying questions; deviations logged as D# entries.
