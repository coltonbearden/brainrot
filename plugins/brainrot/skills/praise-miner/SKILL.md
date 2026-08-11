---
name: praise-miner
description: Mines chat history for praised, zero-correction outputs and extracts the formats and prompt shapes behind them. Use for run praise miner, what works well, success patterns. Outputs do-more rules.
---

# praise-miner

## Purpose

Mine the user's chat history for assistant outputs that drew praise and needed zero corrections, open those threads to find the structural antecedents that preceded first-try success, and codify repeated antecedents into do-more rules. Praise is evidence about what to repeat — never a record of a user decision. An optional final step stages the rules into memory behind an explicit confirm gate.

## Triggers

Run this skill when the user says `run praise miner`, `praise miner`, `what works well`, or `success patterns`. Staging (workflow step 7) runs only on a further explicit `stage rules`.

## Preconditions

- Past-chats tools must be available: `conversation_search`, `recent_chats`, `read_conversation`. If any is missing, say so and stop.
- Run in a chat outside any Project; project chats search only project-scoped history.
- `conversation_search` is a literal keyword match — one search per term, no operators. In-thread probes use `within_conversation_id`.
- `recent_chats` returns at most 20 chats per call. If ≤5 paginated calls do not cover the window, label the report `SAMPLED`.
- Snippets truncate. Antecedents come only from opened threads, never from snippets.
- Memory staging edits `memory_user_edits` (30-entry cap): rules must condense to ≤5 dense lines and execute only behind the confirm gate.

## Lexicon

| Positive terms | Strength |
|---|---|
| perfect | strong |
| exactly what | strong |
| ship it | strong |
| nailed | strong |
| first try | strong |
| works great | strong |
| love it | medium |
| that works | medium |
| beautiful | medium |
| exactly | weak — pairing rule |
| great | weak — pairing rule |

**Pairing rule:** weak terms count only when the snippet shows the praise directed at an assistant output (not at a third party or the user's own work).

## Clean-check

A praised chat is `CLEAN` only if two negative probes inside it return zero hits: `conversation_search(query="no I said", within_conversation_id=<uuid>)` and `conversation_search(query="wrong", within_conversation_id=<uuid>)`. Any hit → `MIXED` (still logged, weighted half).

## Antecedent dimensions

`FORMAT` (table / code block / file artifact / inline prose) · `PROMPT-SHAPE` (spec-first? constraints enumerated? examples given? gates requested?) · `DELEGATION` (answered in chat vs produced a build prompt vs produced files) · `LENGTH` (terse vs long) · `GATES-PRESENT` (verification steps included?)

Record all five for every extracted chat.

## Workflow

1. **Window.** Default lookback 30 days; honor a user-stated override. Enumerate chats with `recent_chats(sort_order="desc", n=20)`, paginating with `before` set to the earliest `updated_at` of the prior batch, at most 5 calls. Record coverage: window requested, chats enumerated, earliest chat reached. If the window is not fully covered, mark the report `SAMPLED`.
2. **Sweep.** For each lexicon term run exactly one `conversation_search(query=<term>, max_results=10)`. Keep hits whose `updated_at` falls inside the window. Dedupe by chat url, keeping the strongest term per chat. Apply the pairing rule before counting any weak-term hit. Candidates whose praise concerns sensitive personal content are set aside and tallied as `SKIPPED-SENSITIVE`.
3. **Clean-check.** Apply the Clean-check to every remaining candidate. Build the table `chat | praise term | CLEAN|MIXED`. `MIXED` chats stay in the table, count half in praise tallies, and are excluded from extraction.
4. **Extract.** Take up to 5 `CLEAN` chats, most recent first. For each, open the thread via `read_conversation` at the praise hit's `page_token` and page back to the originating request; record all five antecedent dimensions from what is actually on the page. GATE: no antecedent row without an actual open — snippet-only inference is forbidden. A thread that fails to open is dropped from extraction and noted in the report.
5. **Codify.** Aggregate antecedent values across extracted chats. A do-more rule requires the same antecedent value in ≥2 CLEAN chats. Emit the rules table `antecedent | evidence count | rule draft (dense, memory-ready)`; all rule drafts together must fit in ≤5 dense lines. Values below the threshold go to the observations list only — never to rules.
6. **Provenance gate.** Re-check every rule draft: rules describe what to do more of; they never assert the user "decided" anything. Praise that landed on an assistant self-suggestion made in passing is excluded from evidence. Fix or drop any draft that fails this gate.
7. **Optional staging.** Only on explicit `stage rules`: run `memory_user_edits view` and record the current state as E0; present a plan with the exact expected post-state E1 (E0 plus the ≤5-line rules block, within the 30-entry cap); wait for explicit user confirmation; execute; re-run view. GATE: observed state == E1 — on mismatch, report the diff and stop.
8. **Report.** Emit, in order: clean-check table, rules table, observations list, coverage line. Use the output template.

## Output template

```
PRAISE MINER — <date>
Window: <start> → <end> · <n> chats enumerated[ · SAMPLED]

Clean-check
| chat | praise term | CLEAN|MIXED |
|---|---|---|
| <url> | <term> | CLEAN |

Do-more rules (same antecedent value in ≥2 CLEAN chats)
| antecedent | evidence count | rule draft |
|---|---|---|
| FORMAT = table | 2 | <dense, memory-ready line> |

Observations (below threshold — not rules)
- <DIMENSION = value> — 1 chat (<url>)

Coverage: <k> sweeps · <c> candidates · <n> CLEAN · <m> MIXED · <s> SKIPPED-SENSITIVE
```

## Guardrails

- Never promote praise into a decision or standing preference without the ≥2-chat threshold.
- Politeness ("thanks") is not praise; require an evaluative term.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- Zero CLEAN chats → report the MIXED table and stop; no fabricated rules.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Memory backend:** `memory_user_edits` and the userMemories block exist on the claude.ai app. Elsewhere, target the agreed memory file (default `~/.claude/CLAUDE.md`, rules section) with the same line budget and the same explicit confirm gates. See `docs/surfaces.md`.
