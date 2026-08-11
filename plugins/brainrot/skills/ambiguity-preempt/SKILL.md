---
name: ambiguity-preempt
description: Finds clarify-loops and wrong guesses in chat history, clusters ambiguity axes, drafts standing disambiguation rules. Use for run ambiguity audit, disambiguation rules, stop asking which.
---

# Ambiguity Preempt

## Purpose

Audit past conversations for two failure shapes: clarify-loops (the assistant had to ask "which one?") and wrong-guess-then-corrected sequences (the assistant picked an instance, the user corrected it). Cluster the incidents by ambiguity axis (machine, account, repo, path, shell, surface, other), then draft standing disambiguation rules — default + inline-statement + ask-only-if-destructive — condensed into a memory-paste block the user can adopt, with optional gated staging into memory edits.

## Triggers

Run this skill when the user says any of:

- `run ambiguity audit`
- `disambiguation rules`
- `stop asking which`
- `ambiguity preempt`

`stage rules` triggers only the optional staging step (Workflow step 7), and only after an audit in the current conversation has produced a rules table.

## Preconditions

- Requires the past-chats tools: `conversation_search`, `recent_chats`, `read_conversation`. If any is unavailable, say so and stop.
- Chats inside Projects are invisible from outside Projects (and vice versa). For a global audit, run in a new chat outside any Project; if scope is limited, state it in the report.
- Staging (step 7 only) additionally requires the `memory_user_edits` tool, which is capped at 30 total edits — this is why rules are condensed to at most one dense line per axis.

## Lexicon (TUNABLE)

`conversation_search` is a literal keyword match, not semantic. Sweep with one search per term, using each short literal phrase exactly as written. Add user-specific terms if the user supplies them.

| Clarify-loop terms | Wrong-guess terms |
|---|---|
| which one | not that one |
| which machine | the other one |
| which account | other account |
| which repo | other machine |
| which folder | wrong repo |
| which version | wrong machine |
| did you mean | wrong folder |
| do you mean | meant the other |
| clarify | — |

## Axis table (TUNABLE)

Instances below are seeds only — axis instances are user-specific and drift. When userMemories is present at runtime, re-derive the instance lists from it (the user's actual machines, accounts, repos, paths, shells, surfaces) before clustering; keep the axis names stable.

| Axis | Seed instances |
|---|---|
| MACHINE | laptop vs desktop vs remote dev box |
| ACCOUNT | work vs personal account on the same service |
| REPO/PROJECT | active project set |
| PATH | canonical projects root vs deprecated roots |
| SHELL/ENV | bash vs zsh vs PowerShell |
| SURFACE | claude.ai vs Claude Code vs Claude Desktop |
| OTHER | anything recurring outside the above |

## Rule form

Every drafted rule must match this form exactly:

`When <axis> is unspecified, default to <value>; state the chosen default inline in the response; ask only if the action is destructive or irreversible.`

## Workflow

Execute in order. Gates are mandatory; do not skip or reorder.

1. **Window.** Default lookback 30 days (user may override). Recipe: `recent_chats` with `sort_order='desc'`, `n=20`, paginating with `before` set to the earliest `updated_at` of the prior batch; stop after at most 5 calls (the tool caps at 20 chats per call). If 5 calls do not reach the start of the window, record coverage `SAMPLED`; otherwise `FULL`. This step bounds coverage; incidents come from step 2.

2. **Sweep.** Run one `conversation_search` per lexicon term with `max_results=10`. Dedupe hits by chat url. Discard hits clearly outside the window. Classify each remaining hit from its snippet:
   - `CLARIFY-LOOP` — the assistant asked which instance the user meant.
   - `WRONG-GUESS` — the assistant guessed an instance and the user corrected it.
   If the snippet is ambiguous, either open the chat once with `read_conversation` at the hit's `page_token` (budget: at most 2 opens per axis) or discard the hit. Never classify on guesswork.

3. **Cluster.** Assign each incident exactly one axis from the axis table (instances re-derived per the runtime note). Build the incidents table:

   `axis | type | count | example (paraphrase) | chats`

   Examples are paraphrased, never quoted verbatim.

4. **Threshold.** Draft a rule only for axes with ≥2 incidents. EXPECT: every drafted rule cites ≥2 incident chats — a candidate that cannot cite 2 does not qualify. Axes with exactly 1 incident go to the watch list, not the rules table.

5. **Draft.** One rule per qualifying axis, in the Rule form exactly. Choose `<value>` by strict priority:
   1. An explicit canonical stated in userMemories (e.g., a declared primary machine or default account).
   2. Otherwise the most frequent corrected-to value across that axis's incidents.
   3. Otherwise write `DEFAULT NEEDED — user to fill` as the value; such rules are flagged in the report and are never staged.

6. **Condense.** Produce (a) the rules table and (b) a single memory-paste block: at most 1 dense line per axis, at most 6 lines total. Each line must be self-contained so the user can paste it into memory edits by hand.

7. **Optional staging (gated).** Only when the user says `stage rules`. Rules containing `DEFAULT NEEDED` are never staged.
   1. `memory_user_edits view` → record the current edit count as E0.
   2. Plan the additions; compute expected count E1 = E0 + number of rules to stage. If E1 > 30, stop and report the cap.
   3. Show the plan (each exact line to be added) and ask for explicit confirmation. No confirmation → do not execute.
   4. Execute the adds, then `memory_user_edits view` again. GATE: observed count == E1. On mismatch, report the discrepancy and stop; never retry silently.

8. **Report.** Output in this order: incidents table, rules table, memory-paste block, watch list, coverage line.

## Output template

```
## Ambiguity audit — <window>

### Incidents
| axis | type | count | example (paraphrase) | chats |
|---|---|---|---|---|
| MACHINE | WRONG-GUESS | 3 | assumed laptop; user meant workstation | url, url, url |

### Drafted rules
| axis | rule |
|---|---|
| MACHINE | When MACHINE is unspecified, default to <value>; state the chosen default inline in the response; ask only if the action is destructive or irreversible. |

### Memory-paste block
<one dense line per qualifying axis, ≤6 lines total>

### Watch list
- <axis> — 1 incident (<chat url>) — below threshold, monitor.

Coverage: FULL|SAMPLED · window <N>d · <chats swept> chats · SKIPPED-SENSITIVE: <n>
```

## Guardrails

- Never invent a default the evidence doesn't support — `DEFAULT NEEDED` is the honest cell.
- A drafted default never overrides an explicit user instruction in a live conversation.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- Zero qualifying axes → report cleanly, stop.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Memory backend:** `memory_user_edits` and the userMemories block exist on the claude.ai app. Elsewhere, target the agreed memory file (default `~/.claude/CLAUDE.md`, rules section) with the same line budget and the same explicit confirm gates. See `docs/surfaces.md`.
