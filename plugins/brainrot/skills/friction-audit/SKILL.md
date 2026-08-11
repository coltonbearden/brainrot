---
name: friction-audit
description: Mines chat history for user frustration and correction patterns. Use for run friction audit, what annoys me, find my complaints. Ranks patterns and stages one fix per pattern.
---

# friction-audit

## Purpose

Sweep the user's chat history over a bounded window for friction: moments where the user corrected Claude, repeated themselves, or pushed back. Cluster the hits into a behavior taxonomy, rank the patterns by weighted frequency, and propose exactly one remediation per pattern. Optionally — and only behind an explicit confirm gate — stage `MEMORY-EDIT` remediations with `memory_user_edits`. The audit is read-only by default and reports only what was actually observed; it never extrapolates.

## Triggers

Run this skill when the user says any of:

`run friction audit` · `what annoys me` · `find my complaints` · `frustration audit` · `friction patterns`

Modifiers the user may add: `7d` (tighten the window to 7 days; default 30) and `stage fixes` (enable Workflow step 7).

## Preconditions

- Tools required: `recent_chats`, `conversation_search`, `read_conversation`. Optional staging additionally requires `memory_user_edits`.
- Scope: chats inside a Project are invisible from outside it. Run in a chat outside any Project for a global sweep, or inside a Project to audit only that Project. State the active scope in the report header.
- `conversation_search` is a literal keyword match. Query each lexicon term verbatim; never add dates or meta-words ("conversation", "yesterday") to a query.
- `recent_chats` returns at most 20 chats per call; treat 5 calls as the practical budget.
- Search hits are snippets and may truncate mid-turn. Attribute text to a speaker only when the `Human:` or `Assistant:` label is visible in the snippet.
- No writes of any kind unless the Workflow step 7 confirm gate passes.

## Lexicon

Run one search per term, query = the term verbatim. This table is tunable: the user may add or remove terms before a run; otherwise use it exactly as written.

| Term (one search each) | Strength |
|---|---|
| no I said | strong |
| that's not what | strong |
| you ignored | strong |
| I already told | strong |
| not what I asked | strong |
| still wrong | strong |
| re-read | medium |
| stop doing | medium |
| why did you | medium |
| didn't ask | medium |
| as I said | medium |
| you keep | medium |
| wrong path | medium |
| undo that | medium |
| again | weak — pairing rule required |
| wrong | weak — pairing rule required |

**Pairing rule:** weak terms count only if the snippet also shows a second lexicon marker or an imperative correction; otherwise discard the hit.

## Taxonomy

`FORMAT` (unwanted bullets/length/structure) · `PATH-VAGUE` (missing absolute paths/targets) · `ASSUMPTION` (acted without ground truth) · `IGNORED-INSTRUCTION` · `VERBOSITY-PREAMBLE` · `HALLUCINATION` (note: deep-dive belongs to claim-audit if installed) · `TOOL-MISUSE` · `SCOPE-CREEP` · `OTHER`

Assign exactly one label per kept hit, judged from the snippet. Ambiguous → `OTHER`, never force-fit.

## Workflow

Execute in order; state each GATE result before moving past it.

1. **Window.** Default 30 days ending today; use 7 days if the user said `7d`. Bound the window with `recent_chats` (`sort_order='desc'`, `n=20`; paginate with `before` = the earliest `updated_at` of the previous batch; at most 5 calls). Record `C` = chats seen inside the window, and coverage = `FULL` if pagination reached past the window start (or exhausted all chats), else `SAMPLED`. **GATE:** state the window bounds, `C`, and coverage before sweeping.
2. **Sweep.** Run one `conversation_search` per lexicon term with `max_results=10`. Dedupe hits by chat url (at most one hit per pattern per chat). Apply the pairing rule to weak terms. Discard hits whose `updated_at` predates the window.
3. **Cluster.** Give each kept hit one taxonomy label from its snippet. Ambiguous → `OTHER`; never force-fit.
4. **Rank.** Score each pattern = hit count × recency weight (most recent hit ≤7d old → ×3; otherwise ≤30d → ×1). Output the ranked table: `pattern | hits | recency | example (short paraphrase) | chats (title+url)`.
5. **Evidence.** For the top 3 patterns only: open at most 2 hits each with `read_conversation` (real conversation id + that hit's `page_token`) to confirm the paraphrase is fair. Cite chat title + url; paraphrase only.
6. **Remediate.** Propose exactly one primary remediation per pattern, typed: `MEMORY-EDIT` (draft the exact dense line to store) / `SKILL-CANDIDATE` (skill name + one-line purpose) / `PROMPT-PATTERN` (what to include in future prompts). **GATE:** exactly one primary remediation per pattern.
7. **Optional staging.** Only if the user said `stage fixes`: run `memory_user_edits` with `view` and record `E0` = current edit count; present the staging plan (the exact lines to add and expected `E1 = E0 + additions`, with `E1 ≤ 30`); require an explicit user confirm; on confirm, execute the adds; run `view` again. **GATE:** observed count == `E1`; on mismatch, report the discrepancy and stop. Without an explicit confirm, write nothing.
8. **Report.** Emit the ranked table, the remediation table, and the coverage line `C chats, FULL|SAMPLED`. If coverage is `SAMPLED`, present counts as lower bounds; no silent extrapolation beyond sampled counts.

## Deep mode

If a conversations export is available — `conversations.json` under `/mnt/user-data/uploads/` on claude.ai, or any path the user supplies (including one produced by `scripts/cc_history_export.py`) — prefer a full-history Python pass over the search sweep. It replaces steps 1–2; the coverage line becomes `N conversations, FULL (export)`.

```python
import json, re

LEXICON = ["no I said", "that's not what", "you ignored", "I already told",
           "not what I asked", "still wrong", "re-read", "stop doing",
           "why did you", "didn't ask", "as I said", "you keep",
           "wrong path", "undo that", "again", "wrong"]

convs = json.load(open("/mnt/user-data/uploads/conversations.json"))
rows = []
for c in convs:                      # each has: name, uuid, chat_messages[]
    counts, human_turns = {}, 0
    for m in c.get("chat_messages", []):
        if m.get("sender") != "human":
            continue
        human_turns += 1
        text = m.get("text") or ""
        for term in LEXICON:
            if re.search(re.escape(term), text, re.IGNORECASE):
                counts[term] = counts.get(term, 0) + 1
    if counts:
        density = sum(counts.values()) / max(human_turns, 1)
        rows.append((c.get("name"), c.get("uuid"), counts, density))
rows.sort(key=lambda r: r[3], reverse=True)   # top conversations by hit density
```

Apply the pairing rule to weak-term matches using the full turn text, report the top conversations by hit density, then continue at Workflow step 3 with the matched human turns as hits. If parsing fails, fall back to the search sweep (step 2) and note the fallback.

## Output template

```
Friction audit — {start}→{end} ({7d|30d}), scope: {global | Project "name"}
Coverage: {C} chats, {FULL|SAMPLED}

Ranked patterns
| pattern | hits | recency | example (short paraphrase) | chats (title+url) |
|---|---|---|---|---|

Remediations — one per pattern
| pattern | type | remediation |
|---|---|---|

Skipped as sensitive: {n} hit(s) counted as SKIPPED-SENSITIVE.   (omit line if zero)
Memory staging: E0={n} → E1={m}, verified.                       (only if staging ran)
```

## Edge cases

- Window not fully covered within 5 `recent_chats` calls → coverage = `SAMPLED`; say so and treat counts as lower bounds.
- Snippet shows no `Human:` label → do not attribute the text; keep the hit only if context still clearly shows a user-side correction, otherwise discard it.
- The same chat surfaces under multiple terms → dedupe by chat url: at most one hit per pattern per chat.
- Run inside a Project → the sweep covers only that Project; the scope line must say so.
- Staging would exceed the 30-edit cap → trim the plan, list the dropped lines, and recompute `E1` before asking to confirm.
- Export present but unparseable → fall back from Deep mode to the search sweep and note the fallback.
- Zero hits → see Guardrails; stop after the one-line report.

## Guardrails

- Sensitive personal content (health, grief, crisis): exclude from the report; count only as `SKIPPED-SENSITIVE`.
- Paraphrase evidence; never reproduce long verbatim passages.
- Read-only unless the Workflow step 7 confirm gate passes.
- Zero hits → report "no friction markers found in window" and stop; do not pad findings.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Memory backend:** `memory_user_edits` and the userMemories block exist on the claude.ai app. Elsewhere, target the agreed memory file (default `~/.claude/CLAUDE.md`, rules section) with the same line budget and the same explicit confirm gates. See `docs/surfaces.md`.
