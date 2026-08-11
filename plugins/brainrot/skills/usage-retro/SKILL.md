---
name: usage-retro
description: "Builds a sampled 7 or 30 day usage retrospective: thread counts, correction rate, delegation ratio, trends, top actions. Use for run usage retro, weekly retro, monthly retro."
---

# usage-retro

## Purpose

Build a 7-day or 30-day retrospective of the user's Claude usage from their chat history: thread count, correction rate, delegation ratio, positive rate, and top topics — with trend deltas against a prior retro file and a top-3 actions table — written to a dated file the user can attach next period as the baseline.

Every rate this skill produces is sampled via keyword probes over search, never exhaustively counted. Honest denominators are the identity of this skill: report what was measured, mark what was capped, and never estimate what the tools cannot see.

## Triggers

Run this skill when the user says:

- `run usage retro`
- `usage retro`
- `weekly retro` (forces the 7-day window)
- `monthly retro` (30-day window)

## Preconditions

- The past-chats tools `recent_chats` and `conversation_search` must be available. If either is missing, say the retro cannot run, and stop.
- Scope follows where the skill runs: chats inside Projects are invisible from outside a Project. Run in a chat outside any Project for the general retro; running inside a Project yields a per-Project retro — label the output header accordingly.
- There is no cross-session state. Trend diffing works only if the user attached a prior `RETRO-*.md` to this conversation; never reconstruct a baseline from memory.
- The report must be written to `/mnt/user-data/outputs/` and presented, so the user can save it and attach it next period.

## Metric definitions

| Metric | How measured | Report form |
|---|---|---|
| threads_in_window | `recent_chats` pagination count | exact, or `≥N (capped)` |
| correction_rate | distinct chats hit by probes `no I said` · `that's not` · `wrong` (pairing rule: `wrong` needs a second marker in-snippet) ÷ threads_in_window | `X/N sampled` |
| delegation_ratio | distinct chats hit by probes `Claude Code` · `build prompt` ÷ threads_in_window | `X/N sampled` |
| positive_rate | distinct chats hit by probes `perfect` · `ship it` · `works great` ÷ threads_in_window | `X/N sampled` |
| top_topics | top 5 recurring content nouns across chat titles from the `recent_chats` pass | list, counts |

`conversation_search` returns top hits, not exhaustive counts: every probe count is a lower bound on the true number of matching chats.

## Anti-fabrication rules

These rules are mandatory. When a rule and a cleaner-looking number conflict, the rule wins.

- Every rate carries its sampled denominator; never a bare percentage.
- Never extrapolate beyond the window or the sample.
- A metric that cannot be measured with available tools is reported `N/A (not measurable via search)` — not estimated.
- Probe hit counts are lower bounds; state `≥` when the search may have truncated.
- Trend deltas are computed only between identically defined metrics; definition changes reset the baseline and say so.

## Workflow

Execute in order; do not skip gates.

1. **Window.** Use 7 days when triggered by `weekly retro`, otherwise 30 days; compute the window start from today's date. Enumerate chats with `recent_chats` (`sort_order='desc'`, `n=20`), paginating with `before` set to the earliest `updated_at` of the prior batch — at most 5 calls. Stop early once a batch contains a chat older than the window start. Set `threads_in_window` to the number of chats whose `updated_at` falls inside the window, and record coverage:
   - `FULL` — pagination passed the window start within the call budget; the count is exact.
   - `CAPPED` — 5 calls exhausted with every returned chat still inside the window; the count is a lower bound. At 20 chats per call this means `≥100 (capped)`.
   - `SAMPLED` — pagination ended early for any other reason (tool error, short batch); report `≥N`.

   **GATE:** the window and the denominator (with coverage) must be stated before any rate is reported. If `threads_in_window` = 0: report the empty window, write no file, stop.

2. **Probes.** Run each probe string from the metric definitions table as one `conversation_search` call with `max_results=10`. Dedupe hits by chat url. Discard hits whose `updated_at` falls outside the window; a hit that cannot be dated is discarded. Pairing rule: a `wrong` hit counts only when its snippet also contains a second correction marker (for example `no`, `that's not`, or `I meant`).

3. **Compute.** Fill the metrics table under the anti-fabrication rules. Rates are `X/N sampled`; when coverage is not `FULL`, write `X/≥N sampled`. Build `top_topics` from the titles collected in step 1: keep content nouns (drop stopwords and generic words such as "chat", "help", "question") and list the top 5 with counts.

4. **Trend.** If `/mnt/user-data/uploads/` contains a prior `RETRO-*.md` (newest by filename date when several), parse its metrics table and add a delta column: `↑`, `↓`, or `→` by direction, plus the raw change (for example `↓ 7/32 → 6/40`). Diff only identically defined metrics; when a definition changed, write `baseline reset (definition changed)` for that row instead of a delta. When no baseline file is attached, state `no baseline attached` and omit the delta column.

5. **Actions.** Write a top-3 actions table with columns `action | metric it moves | first step`. Every action must trace to a metric measured in this run — no generic advice. **GATE:** exactly 3 rows, each naming a metric from the metrics table.

6. **Write.** Create `/mnt/user-data/outputs/RETRO-<YYYYMMDD>.md` per the file format spec below, then present the file to the user.

7. **Report.** In chat, show only the metrics table and the actions table; point to the file for everything else.

## File format spec

Filename: `RETRO-<YYYYMMDD>.md`, using today's date. Layout (example values shown for a run with a baseline attached):

```
# RETRO-20260810

- Date: 2026-08-10
- Window: 30d (2026-07-11 → 2026-08-10)
- Coverage: FULL
- Scope: all chats outside Projects

## Metrics

| Metric | Value | Δ vs 2026-07-10 |
|---|---|---|
| threads_in_window | 40 | ↑ +8 (32 → 40) |
| correction_rate | 6/40 sampled | ↓ 7/32 → 6/40 |
| delegation_ratio | 10/40 sampled | → 8/32 → 10/40 |
| positive_rate | 11/40 sampled | ↑ 6/32 → 11/40 |

## Top topics

1. topic (count) — up to 5 entries; sensitive entries are counted as SKIPPED-SENSITIVE, never named

## Actions

| Action | Metric it moves | First step |
|---|---|---|
| (exactly 3 rows, each naming a metric) | | |

Method: sampled via keyword probes; lower bounds.
```

When no baseline is attached: drop the Δ column and put `Trend: no baseline attached` on its own line directly under the metrics table. When coverage is not FULL, the header shows it and every rate uses the `X/≥N sampled` form.

## Guardrails

- Sensitive personal content never appears in top_topics or examples; count as `SKIPPED-SENSITIVE`.
- If threads_in_window = 0: report empty window, write no file, stop.
- The skill's numbers inform, never accuse — no psychological framing of the user's behavior.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Paths:** `/mnt/user-data/outputs/` and `/mnt/user-data/uploads/` are claude.ai container paths. Elsewhere, write to the working directory (or a path the user names), read inputs from wherever the user supplies them, and skip the present-file step.
