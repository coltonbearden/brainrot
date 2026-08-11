---
name: rule-drift
description: Audits Claude's adherence to the user's standing rules across recent chats. Use for run rule drift, rule compliance audit, audit my rules. Scores each rule, proposes keep, rewrite, or retire.
---

# rule-drift

Audit Claude's adherence to the user's standing rules, using the user's own recent chat history as evidence. Every rule leaves the audit with exactly one verdict and, wherever wording changes are proposed, the exact drafted replacement line.

## Purpose

Extract the user's standing rules from in-context persistent memory, probe recent chats for violations of each rule, score adherence with evidence, and verdict every rule KEEP / REINFORCE / REWRITE / RETIRE. Optionally stage confirmed changes through a gated `memory_user_edits` sequence. This audits assistant behavior against the user's rules — it never grades the user.

## Triggers

Run this skill when the user says any of: `run rule drift` · `rule compliance audit` · `audit my rules` · `rule drift`.

## Preconditions

These platform realities shape every step; work with them, never around them:

- **Rules live in context, not in a file.** Standing rules sit inside the in-context userMemories block. Parse that block at runtime. If no userMemories block (or no standing-rules content within it) is present in the conversation, say exactly that and stop — do not invent rules and do not mine chat history to reconstruct them.
- **`conversation_search` is a literal keyword matcher.** Probes must be short phrases the *user* would actually type when a rule is broken — corrections and complaints in user-voice — never descriptions of the rule itself.
- **`recent_chats` caps at 20 chats per call.** Default audit window is 30 days. If ≤5 paginated calls cannot reach the window start, coverage is `SAMPLED`; otherwise `FULL`.
- **Some rules are undetectable via search.** A rule whose violation would not provoke a typed user reaction gets `detectable? = N` and the verdict `KEEP (unmeasured)`. Keep the `detectable?` column honest — never fake a measurement.
- **Memory edits are capped and gated.** `memory_user_edits` holds at most 30 edits, and destructive operations need confirmation. RETIRE and REWRITE never execute against memory without explicit per-rule user confirmation, and staging runs only when the user asks for it.

## Probe-design patterns

Derive real probes from the live rule set at extraction time. The table below shows how probes are derived per rule archetype — these rows are worked examples of the pattern, **not** the rule set to audit:

| Rule archetype | Violation probes (what the user says when it's broken) |
|---|---|
| Absolute paths required | `full path` · `which folder` · `where exactly` |
| Single recommendation | `which option` · `pick one` · `too many options` |
| Minimal preamble | `get to the point` · `skip the intro` |
| Delegate multi-step work to a build prompt | `give me a prompt instead` · `should have been a prompt` |
| Reproduce full corrected artifacts | `resend the whole` · `full file please` |
| No assuming work is done | `I never ran` · `not done yet` · `that didn't happen` |

Probe rules: 2–3 probes per detectable rule; 2–4 words each; user-voice corrections only (what a frustrated user types, not what the rule says); content words a violation would provoke — no meta-words like "rule", "memory", or "preference", since those rarely appear in the moment of correction.

## Workflow

Execute in order. Gates block progress until satisfied.

### 1. Extract

Parse the standing-rules section of the in-context userMemories block into:

| rule id | text (condensed) | detectable? (Y/N) | probes |
|---|---|---|---|

- `rule id`: R1, R2, … in memory order.
- `text (condensed)`: one line, intent preserved.
- `detectable?`: Y only if a violation would plausibly provoke a typed user correction findable by literal search.
- `probes`: 2–3 per detectable rule, derived per the patterns above; `—` for undetectable rules.

**GATE:** every `detectable? = Y` rule has ≥2 probes before any sweeping begins. If no memory block exists: say so and stop.

### 2. Window

Default 30 days (the user may override). Establish coverage with `recent_chats`: `sort_order='desc'`, `n=20`, paginate by setting `before` to the earliest `updated_at` of the prior batch, at most 5 calls. Record the earliest chat reached.

- Window start reached → coverage `FULL`.
- Not reached → coverage `SAMPLED`; record the span actually covered.

### 3. Sweep

One `conversation_search` call per probe with `max_results=5`. Then, per rule:

- Dedupe hits by chat url across that rule's probes.
- Count a hit as a **violation** only if the snippet shows the user correcting assistant behavior covered by the rule. Merely discussing the topic is not a violation.
- Unclear snippet → at most one `read_conversation` open at the hit's `page_token`, and ≤2 opens per rule total. Still unclear → discard the hit.
- Hits older than the window → discard.
- Hits inside sensitive personal content → do not open or quote; record `SKIPPED-SENSITIVE` for the affected rule.

### 4. Score

Build the adherence table:

| rule | violations found | last seen | evidence (title+url) |
|---|---|---|---|

- `violations found`: integer after dedupe and confirmation; `unmeasured` for undetectable rules.
- `last seen`: date of the most recent confirmed violation, else `—`.
- `evidence`: up to 3 entries per rule, chat title + url.

### 5. Verdict

Assign exactly one verdict per rule using the Verdict definitions below. Every REINFORCE and REWRITE ships the exact replacement line in the verdict table — never "consider rewording", always the finished line.

### 6. Confirm + optional staging

- **RETIRE requires explicit per-rule user confirmation regardless of staging.** Show the rule's full original text when asking; a condensed line is not enough for a deletion decision.
- Staging runs only when the user says `stage changes`:
  1. `memory_user_edits view` → record current edit count `E0`.
  2. Present the plan: every exact add / replace / remove line, and the expected post-count `E1` (must be ≤30 — if it would exceed the cap, stop and say so).
  3. Wait for explicit user confirmation of the plan.
  4. Execute the confirmed edits.
  5. `memory_user_edits view` again. **GATE:** observed count == `E1` and lines match the plan. On mismatch: report the discrepancy verbatim and stop — never patch silently.

### 7. Report

Emit in order: adherence table → verdict table with drafts → coverage line (`FULL`/`SAMPLED`, span, chat count, plus the sampling caveat from Guardrails whenever coverage is `SAMPLED`) → `SKIPPED-SENSITIVE` count if any.

## Verdict definitions

| Verdict | Condition | Ships with |
|---|---|---|
| `KEEP` | 0 confirmed violations and the rule is still relevant | — |
| `KEEP (unmeasured)` | `detectable? = N` — honesty over false confidence | — |
| `REINFORCE` | ≥1 confirmed violation; wording is fine but adherence slipped | exact strengthened replacement line |
| `REWRITE` | rule unclear, ambiguous, or partially obsolete | exact replacement line |
| `RETIRE` | zero relevance in the window AND explicit user confirmation received | full original text shown at confirmation |

Routing order per rule: undetectable → `KEEP (unmeasured)`; else zero relevance in window → `RETIRE` (report as `RETIRE (pending confirm)` until the user confirms); else wording unclear or partially obsolete → `REWRITE`; else ≥1 confirmed violation → `REINFORCE`; else `KEEP`.

## Output template

Use this exact structure:

```
# Rule drift audit — {date}
Window: {start} → {end} · Coverage: {FULL|SAMPLED} ({n} chats)

## Adherence
| rule | violations found | last seen | evidence |
|---|---|---|---|
| R1 {condensed text} | 2 | {date} | {title} ({url}) |
| R2 {condensed text} | unmeasured | — | — |

## Verdicts
| rule | verdict | draft |
|---|---|---|
| R1 | REINFORCE | "{exact replacement line}" |
| R2 | KEEP (unmeasured) | — |
| R3 | RETIRE (pending confirm) | original shown below |

{RETIRE confirmations: one block per rule, full original text, explicit yes/no question}
{if SAMPLED: sampling caveat from Guardrails}
{if any: SKIPPED-SENSITIVE: n}
```

## Guardrails

- Absence of violation evidence is not proof of compliance under `SAMPLED` coverage — say so in the report.
- Never RETIRE silently; never merge two rules without showing both originals.
- Drafted rewrites must preserve the rule's intent; intent changes are flagged `INTENT-CHANGE` for the user.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Memory backend:** `memory_user_edits` and the userMemories block exist on the claude.ai app. Elsewhere, target the agreed memory file (default `~/.claude/CLAUDE.md`, rules section) with the same line budget and the same explicit confirm gates. See `docs/surfaces.md`.
- When the backend is a memory file, extract the rule set from that file's rules section instead of the userMemories block.
