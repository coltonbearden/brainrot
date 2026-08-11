---
name: claim-audit
description: Finds facts Claude asserted then the user corrected. Use for run claim audit, hallucination audit, what did you get wrong. Root-causes incidents, outputs prevention and search-first rules.
---

# Claim Audit

## Purpose

Locate facts Claude asserted in past conversations that the user then corrected. Root-cause each confirmed incident, then output a prevention ruleset — search-first triggers and verification gates — so the same class of error stops recurring. Optionally stage those rules into persistent memory, but only behind an explicit confirmation gate.

## Triggers

Run this skill when the user says `run claim audit`, `hallucination audit`, `what did you get wrong`, `claim audit`, or otherwise asks to find Claude's past incorrect claims and build rules to prevent them.

## Preconditions

- Run outside any Project for a global audit. Chats inside a Project are invisible to conversation search from outside it (and vice versa). If invoked inside a Project, state up front that coverage is limited to that Project's chats.
- Required tools: `conversation_search`, `recent_chats`, `read_conversation`. Optional: `memory_user_edits` (staging step only), Python + file access (deep mode only).
- Default audit window: last 30 days. The user may widen or narrow it.

## Lexicon

`conversation_search` is a literal keyword match, not semantic. Run exactly one search per term below — never merge terms into a single query, and keep phrasing as the content words users actually type when correcting.

| Term (one search each) |
|---|
| actually it's |
| that's wrong |
| doesn't exist |
| no such |
| not a real |
| hallucinat |
| made that up |
| outdated |
| wrong version |
| deprecated |
| that flag |
| that API |
| invented |
| check again |

Tunable: append user-suggested terms as additional single-term searches with the same content-noun phrasing.

## Incident schema and enums

Schema: `id | asserted claim (paraphrase) | correction (paraphrase) | domain | root cause | chat (title+url)`

Domains: `VERSION` · `API/FLAG` · `PATH/CONFIG` · `PRODUCT-FEATURE` · `FACT` · `OTHER`

Root causes (assign exactly one per incident):
`STALE-TRAINING` (world moved past training data) · `UNVERIFIED-ASSUMPTION` (guessed instead of checking context) · `SKIPPED-SEARCH` (should have searched, didn't) · `OVERCONFIDENT-SYNTHESIS` (combined true facts into a false one) · `CONTEXT-MISREAD` (info was in-thread, misread)

## Workflow

1. **Window.** Establish coverage with `recent_chats`: `sort_order='desc'`, `n=20`, then paginate by setting `before` to the earliest `updated_at` of the prior batch. Stop at 5 calls (≤100 chats). If the window is not fully covered by then, label the run `SAMPLED` and report the range actually covered; otherwise `FULL`.
2. **Sweep.** Run one `conversation_search` per lexicon term with `max_results=10`. Dedupe hits by chat url; drop hits outside the window. Keep a hit only when the correction sits in a human turn — the `Human:` label must be visible on it in the snippet. Snippets can truncate mid-turn and text before the first label is unattributable: if attribution is unclear, either verify with one `read_conversation` open at the hit's `page_token`, or discard the hit. Never root-cause an unconfirmed hit.
3. **Log.** Fill one schema row per confirmed incident. Recover the asserted claim from the assistant turn preceding the correction, opening the chat if the snippet lacks it — at most 2 `read_conversation` opens per incident, always with the real conversation id and the hit's `page_token` (never a guessed id). Paraphrase all evidence; do not quote at length. GATE: every logged row has both a claim cell and a correction cell. A correction whose original claim is unrecoverable within budget goes to the `UNPAIRED` list, not the log.
4. **Root-cause.** Assign exactly one root-cause enum value per incident, with a one-clause justification (e.g. `STALE-TRAINING — flag was renamed after the training window`).
5. **Prevent.** From the root causes actually present in the log, emit only the matching rules from the prevention mapping below. Condense to ≤5 dense lines total, each standalone, imperative, and memory-paste-ready. Root causes not present emit nothing.
6. **Optional staging.** Only when the user explicitly says `stage rules`. Run `memory_user_edits view`; record the current edit count as E0. Present a plan: the exact lines to add and the expected post-count E1 (the cap is 30 edits — consolidate lines rather than exceed it, and never remove or replace existing edits without the user asking). Require explicit confirmation of the plan. On confirm, add the lines, then `view` again. GATE: observed count == E1; on mismatch, report the discrepancy and stop.
7. **Report.** Emit the output template: incident log, root-cause distribution counts, prevention lines, UNPAIRED list, coverage line.

## Prevention mapping

| Root cause | Prevention rule to draft |
|---|---|
| STALE-TRAINING | Search before asserting versions, flags, APIs, product features, prices, or current status |
| UNVERIFIED-ASSUMPTION | State the assumption + confidence inline, or verify before acting |
| SKIPPED-SEARCH | Concrete search-first trigger list: anything post-cutoff, anything the user could disprove with one lookup |
| OVERCONFIDENT-SYNTHESIS | Flag inferred (vs sourced) claims explicitly as inference |
| CONTEXT-MISREAD | Re-read the exact user turn before contradicting or restating it |

## Deep mode

If a conversations export exists — `/mnt/user-data/uploads/conversations.json` on claude.ai, or any path the user supplies (including one produced by `scripts/cc_history_export.py`): Python pass — `json.load`; per conversation iterate `chat_messages`; regex lexicon over `sender == "human"` turns; pair each hit with the immediately preceding assistant turn as the claim candidate; output pairs for manual confirmation. Fallback to search sweep on parse failure.

## Output template

```
# Claim Audit — {date}
Coverage: {window} · {chats seen} chats · {FULL|SAMPLED}

## Incidents
| id | asserted claim | correction | domain | root cause | chat |
|---|---|---|---|---|---|
{one row per confirmed incident; "none" if empty}

## Root-cause distribution
{ENUM: count · ENUM: count · ...}

## Prevention rules (memory-paste-ready)
{≤5 lines, only for root causes present}

## UNPAIRED
{correction paraphrase + chat, one line each; "none" if empty}

{Skipped (sensitive): n — only if n > 0}
{Staging: E0={n} → E1={n} confirmed — only if staging ran}
```

## Guardrails

- Never fabricate the "asserted claim" cell; if unrecoverable, the row is UNPAIRED.
- User corrections are treated as ground truth for logging, but note when a correction itself looks uncertain.
- Sensitive personal content: exclude; count as `SKIPPED-SENSITIVE`.
- Zero incidents → report cleanly, no padding.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Memory backend:** `memory_user_edits` and the userMemories block exist on the claude.ai app. Elsewhere, target the agreed memory file (default `~/.claude/CLAUDE.md`, rules section) with the same line budget and the same explicit confirm gates. See `docs/surfaces.md`.
