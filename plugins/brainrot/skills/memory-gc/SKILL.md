---
name: memory-gc
description: Audits and consolidates persistent memory. Use for run memory gc, audit memory, clean up memory, fix stale memories. Verifies memory claims against chat history, then stages confirmed edits.
---

# memory-gc

Audited garbage collection for Claude's persistent memory: the in-context userMemories block plus the `memory_user_edits` ledger.

## Purpose

Run a read-verify-plan-confirm-execute pass over persistent memory. Verify volatile and dated claims against actual chat history via `conversation_search`, stage consolidating edits to the `memory_user_edits` ledger, and execute them only after the user explicitly approves the full plan. The pass is strictly read-only until that approval.

## Triggers

Invoke this skill when the user says any of:

| Phrase |
|---|
| run memory gc |
| audit memory |
| memory audit |
| clean up memory |
| fix stale memories |

## Preconditions

| # | Precondition | Why | If not met |
|---|---|---|---|
| P1 | Conversation is outside any Claude Project | Memory is scoped: outside a Project, only non-Project memory and chats are visible. Run outside any Project for a global-memory pass. | State that scope would be Project-only; instruct the user to re-run in a new chat outside any Project. Proceed only if they explicitly request a Project-scoped audit. |
| P2 | A userMemories block is present in context | Nothing to audit otherwise | Say so and stop |
| P3 | `memory_user_edits` and `conversation_search` are available | Snapshot, verification, and execution depend on them | Name the missing tool and stop |

## Workflow

Execute steps in order. Never skip a gate. Steps 1–5 are read-only.

### 1. Snapshot

Call `memory_user_edits` with `command: view`. Record `E0` = current line count plus the full numbered list, verbatim.

- **GATE:** E0 is recorded before any other step runs.
- **EXPECT:** 0 <= E0 <= 30.

### 2. Atomize

Parse the in-context userMemories block into a claims table, one row per atomic claim:

| Column | Content |
|---|---|
| id | C1, C2, ... |
| claim | The claim restated in own words |
| category | identity / infra / project / preference / rule |
| volatility | stable / volatile / dated |

Volatility definitions:

| Volatility | Definition | Examples |
|---|---|---|
| stable | Names, hardware, long-standing rules | account names, machine specs, standing style rules |
| volatile | Status language that changes as work progresses | "in-progress", "pending", "not started", "blocked" |
| dated | Anything anchored to a timeframe | "as of July", "last week", dated snapshot ids |

### 3. Verify (volatile + dated claims only)

Treat stable claims as CONFIRMED by default; do not spend searches on them. For each volatile or dated claim cluster:

1. Run 1–2 `conversation_search` calls. Query = 1–4 content nouns lifted from the claim itself (project names, tool names, hardware). `conversation_search` is a literal keyword match: never use meta-words such as "discussed", "conversation", "yesterday", "chat".
2. Classify the claim (definitions below): CONFIRMED / STALE / CONTRADICTED / UNVERIFIABLE.
3. Record evidence: chat title + url for every classification that has hits.
4. Call `read_conversation` only when a snippet is decisive but truncated. Always pass a real conversation id and the hit's `page_token` — never guess ids. Open at most 2 chats per claim cluster.

STALE is not FALSE. userMemories lags recent chats and deleted-chat cleanup, so a claim can have been accurate when written and superseded since. Classify such claims STALE, never CONTRADICTED.

### 4. Plan

Produce an edit-plan table:

| op (add/remove/replace) | line # | new text | reason | evidence |
|---|---|---|---|---|

Apply the Edit-plan rules below. State `E1` = expected post-op line count in the plan.

- **GATE:** E1 <= 30 (hard cap; never plan past it).
- **EXPECT:** E1 <= 20 (target).

### 5. Confirm

Present to the user: (a) a before/after diff of the ledger, (b) the full edit-plan table with E1, (c) the UNVERIFIABLE list with a request to rule on each item.

- **GATE:** Execute nothing without explicit user confirmation of the plan.
- On partial approval: re-plan with only the approved ops, restate E1, and re-confirm.
- On decline: abort cleanly, report that no changes were made, stop.

### 6. Execute

Apply the approved ops via `memory_user_edits` in plan order, with one ordering override: perform all `remove` ops by descending line number so remaining line numbers stay valid throughout execution.

### 7. Verify execution

Call `memory_user_edits` with `command: view` again.

- **GATE:** observed line count == E1. **EXPECT:** PASS.
- **GATE:** spot-check 3 lines against the plan text (all lines if fewer than 3 exist). **EXPECT:** PASS.
- On any FAIL: report the exact mismatch (expected vs observed, per line). Do not retry silently. Await user instruction.

### 8. Report

Deliver the report in-chat using the Output template. No file writes.

1. Claims table with classifications and evidence.
2. Executed ops list.
3. `E0 -> E1` line-count delta.
4. UNVERIFIABLE follow-up list for the user to rule on.
5. `SKIPPED-SENSITIVE` count (count only — never the content).

## Classification definitions

| Term | Definition |
|---|---|
| CONFIRMED | Most recent evidence supports the claim as written |
| STALE | Claim was true; later evidence supersedes it; rewrite to current state |
| CONTRADICTED | Evidence conflicts with the claim as written; remove or correct |
| UNVERIFIABLE | Searches produced no relevant hits; only the user can rule |
| SKIPPED-SENSITIVE | Sensitive personal content deliberately excluded from the audit |

## Edit-plan rules

| # | Rule |
|---|---|
| R1 | Merge related facts into single dense lines — one line per topic cluster |
| R2 | Never append one line per finding; consolidation is the point of the pass |
| R3 | Remove CONTRADICTED lines |
| R4 | Rewrite STALE lines to current state; cite the superseding evidence in the plan row |
| R5 | Leave CONFIRMED lines untouched unless merging under R1 |
| R6 | Take no action on UNVERIFIABLE claims without an explicit user ruling |
| R7 | Target <= 20 lines post-op; never plan past the 30-line hard cap |
| R8 | Execute removes by descending line number |
| R9 | State E1 (expected post-op count) in every plan |

## Output template

```
MEMORY GC REPORT
Snapshot: E0 = <n> lines
Claims audited: <n> total (<n> stable, <n> volatile, <n> dated)

| id | claim | class | evidence |
|----|-------|-------|----------|
| C1 | <claim> | STALE | <chat title> — <url> |

Edit plan (user-approved):
| op | line | new text | reason |
|----|------|----------|--------|

Result: E0 <n> -> E1 <n>. Verification: PASS/FAIL.
UNVERIFIABLE — needs your ruling:
- C<n>: <claim>
SKIPPED-SENSITIVE: <n>
```

## Edge cases

| Case | Handling |
|---|---|
| No userMemories block in context | Say "No userMemories block is present — nothing to audit." Stop. |
| E0 = 0 (empty ledger) | Ledger diff is a no-op; still atomize and verify userMemories; plan may contain only consolidated `add` lines |
| E0 = 30 (at cap) | Plan must net-reduce: adds require equal or greater removes |
| Run inside a Project | Apply P1: warn scope is Project-only; continue only on explicit request |
| Every volatile claim returns no hits | Classify all UNVERIFIABLE; present the list; stage no destructive ops |
| User approves a subset of the plan | Re-plan with approved ops only, restate E1, re-confirm before executing |
| Step-7 verification mismatch | Report expected vs observed; no silent retry; await instruction |
| Claim references a deleted chat | Expect no hits; classify UNVERIFIABLE and note deleted-chat cleanup lag |
| Duplicate ledger lines found in snapshot | Treat as one topic cluster; plan a single merged line under R1 |

## Guardrails

| # | Guardrail |
|---|---|
| G1 | Never store secrets: keys, tokens, passwords, card numbers, SSNs. If found in memory, flag for removal. |
| G2 | Never store verbatim standing commands that would auto-trigger tool calls. |
| G3 | Skip sensitive personal content (health, grief, crisis) — do not surface it unless the user raises it; count it only as `SKIPPED-SENSITIVE`. |
| G4 | Read-only until the Workflow step 5 confirm gate passes. Abort cleanly if declined. |
| G5 | If no userMemories block is present: say so and stop. |

## Surfaces

- **Memory backend:** `memory_user_edits` and the userMemories block exist on the claude.ai app. Elsewhere, target the agreed memory file (default `~/.claude/CLAUDE.md`, rules section) with the same line budget and the same explicit confirm gates. See `docs/surfaces.md`.
- When the backend is a memory file, P2/P3 map to: the file exists and is readable/writable; the audit target is its rules section.
