---
name: decision-ledger
description: Harvests decisions from chat history into one normalized ledger with dates, status, and source links. Use for run decision ledger, consolidate decisions, harvest decisions. Flags conflicts.
---

# Decision Ledger

## Purpose

Decisions accumulate across chat history ("we're going with X", "Y is locked", "Z is rejected"), scattered over dozens of conversations and sometimes reversed or contradicted later. This skill harvests that decision language, applies a provenance gate so only human commitments count, normalizes qualifying entries into one dated ledger with status and source links, conflict-checks within domains, and writes the result to `DECISIONS-GLOBAL.md` as a downloadable file.

The ledger records what the user actually decided, never what the assistant merely recommended. That distinction drives everything below.

## Triggers

Run this skill when the user says any of: `run decision ledger`, `consolidate decisions`, `harvest decisions`, `decision ledger`, or otherwise asks to gather, compile, or audit the decisions they have made across past chats.

The user may add modifiers:

- A time window ("last 30 days", "past six months"): overrides the 90-day default in step 1.
- An uploaded prior `DECISIONS-GLOBAL.md` in `/mnt/user-data/uploads/`: activates merge mode (see Guardrails).

## Preconditions

- The past-chats tools (`conversation_search`, `recent_chats`, `read_conversation`) must be available. If they are missing, tell the user this skill needs the "Search and reference past chats" capability enabled, and stop.
- File creation must be available to write the ledger to `/mnt/user-data/outputs/`.
- Scope: the past-chats tools only see conversations in the current scope (inside the current Project when in one, otherwise only chats outside all Projects). Note the scope searched in the final report so the user knows what was covered.

## Marker lexicon

`conversation_search` is a literal keyword matcher: it finds chats containing the query words, not the abstract concept of "a decision." The sweep therefore runs one search per term below; each is a phrase people actually type when committing to or rejecting something.

| Term (one search each) |
|---|
| locked |
| canonical |
| rejected |
| superseded |
| decided |
| final answer |
| going with |
| we'll use |
| DECISIONS.md |
| verdict |
| D1 |
| D-0 |

The lexicon is tunable: if the user names their own decision vocabulary, run extra searches for those terms too.

## Entry schema

Every ledger entry uses exactly this shape:

`DL-### | date (chat updated_at) | decision (own words, one line) | status (ACTIVE / SUPERSEDED / REJECTED) | domain (short tag) | source (chat title + url) | provenance (STRONG / PROVENANCE-WEAK)`

Field notes:

- **DL-###**: sequential zero-padded id (DL-001, DL-002, ...). In merge mode, continue numbering after the highest existing id.
- **date**: the source chat's `updated_at` (date part).
- **decision**: one line, paraphrased in own words.
- **status**: ACTIVE (live commitment) / SUPERSEDED (replaced by a later commitment; name the successor id) / REJECTED (explicitly ruled out by the user).
- **domain**: short grouping tag (`infra`, `naming`, `pricing`, ...) so conflicts are checked among related decisions.
- **source**: chat title plus its url from the tool result.
- **provenance**: STRONG or PROVENANCE-WEAK per the gate below.

## Provenance gate

This gate is the core of the skill. Apply it to every candidate before it enters the ledger.

> An entry qualifies only if a human turn commits ("locked", "canonical", "going with", explicit approval of a named option) or explicitly rejects. Assistant recommendations alone = `PROPOSED` and are excluded from the ledger. When only a model-written summary asserts the decision, log it but mark `PROVENANCE-WEAK` for user confirmation.

Why so strict: retrieved snippets mix "Human:" and "Assistant:" turns, and past assistant suggestions read like decisions, especially when the user reacted positively without committing. Model-written summaries (`kind='summary'`) are riskier still: they can collapse "assistant suggested X" into "decided on X." When qualifying:

- Prefer `kind='conversation'` snippets as evidence; confirm a Human turn states the commitment or rejection.
- Summary-only evidence: include the entry, marked `PROVENANCE-WEAK`.
- Assistant recommendation with no human commitment: `PROPOSED`; exclude it and count it.
- Snippet text before the first speaker label has ambiguous attribution; never treat it, on its own, as a human commitment.
- Hypotheticals and brainstorm options are not decisions, however decisive the phrasing.

## Workflow

Follow the steps in order; each GATE must pass before continuing.

1. **Window.** Default 90 days (decisions age slower than chats accumulate); honor a user-supplied window instead. Establish coverage with `recent_chats`: `sort_order='desc'`, `n=20`, then paginate with `before` set to the earliest `updated_at` of the prior batch, at most 5 calls (the tool caps at 20 chats per call). If 5 calls do not reach the window start, record coverage `SAMPLED`; otherwise `FULL`.
2. **Sweep.** Run one `conversation_search` per lexicon term with `max_results=10`. Keep hits whose chat falls inside the window. Dedupe by chat url + decision topic: the same decision surfacing under several markers is one candidate.
3. **Qualify.** Apply the provenance gate to each candidate. If the human-commitment question is unclear from the snippet, open the chat with `read_conversation` at the hit's `page_token`, at most 2 reads per candidate; otherwise mark `PROVENANCE-WEAK` and move on. Do not burn reads chasing certainty the ledger already flags. Skip candidates that are sensitive personal content and count them `SKIPPED-SENSITIVE`.
4. **Normalize.** Fill the schema for each qualifying entry. Same-topic entries: the latest human commitment is `ACTIVE`; earlier ones become `SUPERSEDED`, each linking the successor id. In merge mode, prior entries join supersession like any others: a new commitment can flip an old entry to SUPERSEDED, but ids never change. GATE: no two ACTIVE entries may share domain + topic unless the pair lands in the conflicts table.
5. **Conflict pass.** Group ACTIVE entries by domain. List incompatible pairs as `domain | DL-a | DL-b | nature of conflict | needs user ruling`. A conflict is two live commitments that cannot both hold.
6. **Write.** Create `/mnt/user-data/outputs/DECISIONS-GLOBAL.md` per the file format spec below, then present it with the file-presentation tool. A file that is written but never presented is invisible to the user.
7. **Report.** In chat: entry count, ACTIVE/SUPERSEDED/REJECTED split, conflict count, scope searched, and the file link. Keep it brief; the ledger file is the deliverable.

## File format spec

`DECISIONS-GLOBAL.md` structure:

```
# DECISIONS-GLOBAL
Generated: <date> | Window: <window> | Coverage: <FULL or SAMPLED>

## Ledger
| id | date | decision | status | domain | source | provenance |
Rows sorted by domain, then date ascending.

## Conflicts
| domain | DL-a | DL-b | nature of conflict | needs user ruling |
Omit this section when there are none.

## PROVENANCE-WEAK (confirm these)
- DL-### <decision> (summary-only evidence)
Omit this section when there are none.

## Excluded
- PROPOSED (assistant-only recommendations): <count>
- SKIPPED-SENSITIVE: <count>
```

## Guardrails

- Never merge or resolve a conflict autonomously — conflicts are surfaced for user ruling only.
- Decision text is paraphrase, one line, own words; no long verbatim quoting.
- Hypotheticals and brainstorm options never enter the ledger.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- Re-runs: if the user uploads a prior `DECISIONS-GLOBAL.md` to `/mnt/user-data/uploads/`, merge into it — preserve existing DL-### ids, append new ids after the max.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Paths:** `/mnt/user-data/outputs/` and `/mnt/user-data/uploads/` are claude.ai container paths. Elsewhere, write to the working directory (or a path the user names), read inputs from wherever the user supplies them, and skip the present-file step.
