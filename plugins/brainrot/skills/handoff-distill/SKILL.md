---
name: handoff-distill
description: "Distills a session into a canonical handoff: decisions, open items, exact paths, verification state, next-session prompt. Use for handoff, distill this session, prep next session."
---

# handoff-distill

## Purpose

Distill the current session — or a named past chat — into one canonical handoff block: decisions, evidence-backed completions, open items, exact absolute paths, verification state, and a paste-ready next-session prompt. The block is the deliverable; write a file only when the user asks for one. The point is that the next session can start cold and lose nothing.

## Triggers

Invoke on any of: `handoff` · `distill this session` · `prep next session` · `session handoff` · `handoff block`.

## Provenance rule

Only these count as ground truth: explicit user statements, executed tool output visible in the thread, and files/artifacts actually produced. Assistant recommendations, drafts, and plans are `PROPOSED` — never promoted to `DECIDED` or `DONE` without a user commitment in a human turn. Hypotheticals stay hypothetical.

This rule governs every row of the template. The assistant's memory of "done" is unreliable; only evidence visible in-thread makes something Completed. A positive user reaction to a suggestion ("nice", "sounds good") is not a commitment unless it clearly adopts the item.

## Workflow

1. **Scope.** Default = the current conversation; no search needed. If the user names another chat: run `conversation_search` with content nouns from their reference (not meta-words like "chat" or "yesterday"); open the best hit via `read_conversation` with that hit's `page_token`; page adjacent turns only; ≤2 chats total. If the reference is too vague to search, ask which chat — the single permitted question.
2. **Extract.** Fill every section of the Handoff template below, applying the Provenance rule to every row. Classify each candidate item exactly once: Decisions, Completed, Proposed, or Open.
3. **Gate.** Run the four gates below before any output. Anything failing a gate moves to Proposed or Open — never silently dropped. EXPECT: all four gates PASS, stated in one line above the block.
4. **Output.** Emit the handoff block in-chat. File write only on request: `/mnt/user-data/outputs/HANDOFF-<slug>-<YYYYMMDD>.md`, then present it.

## Handoff template (output contract — use this exact structure)

```
## HANDOFF — <title> — <YYYY-MM-DD>
### Decisions (locked)
| id | decision | source (turn/quote paraphrase) |
### Completed (evidence-backed)
| item | evidence (command run / output / file path / url) |
### Proposed (not yet decided)
| item | proposer | status |
### Open items
| id | item | blocker | exact next action |
### Exact paths & environments
| what | absolute path or host | shell/env |
### Verification state
| check | expected | observed | status |
### Next-session prompt
<one paste-ready prompt: goal, constraints, questions front-loaded, all outputs written to files, absolute paths only>
```

## Gates

- (a) Every path in "Exact paths & environments" is absolute — zero shorthand like "the repo".
- (b) Every Completed row has a non-empty evidence cell.
- (c) The Next-session prompt contains zero unresolved placeholders or bracketed TODOs.
- (d) Anything failing a gate moves to Proposed or Open — never silently dropped.

State the result in one line directly above the block, e.g. `Gates: a PASS · b PASS · c PASS · d PASS`.

## Edge cases

- Empty/near-empty session → minimal block with Open items only; say so.
- Conflicting decisions in-thread → latest user statement wins; earlier entry marked `SUPERSEDED` with both sources.
- Session spans multiple projects/topics → one block per topic, max 3, else ask the user to pick.

## Guardrails

- Never fabricate evidence cells; `evidence: none found` is a valid cell that forces the row into Open/Proposed.
- Paraphrase user turns; no long verbatim quoting.
- Sensitive personal content appears in the handoff only if the user raised it as a work item.

## Surfaces

- Current-session distillation works on every surface. The named-past-chat variant needs the past-chats tools; without them, say so and distill the current session only.
- **Paths:** `/mnt/user-data/outputs/` and `/mnt/user-data/uploads/` are claude.ai container paths. Elsewhere, write to the working directory (or a path the user names), read inputs from wherever the user supplies them, and skip the present-file step.
