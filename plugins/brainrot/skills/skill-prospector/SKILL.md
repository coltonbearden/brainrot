---
name: skill-prospector
description: Finds recurring tasks in chat history worth converting into skills. Use for run skill prospector, what skills should I build, skill backlog. Scores candidates, drafts upload-ready descriptions.
---

# Skill Prospector

## Purpose

Mine the user's chat history for task shapes that recur often enough to justify packaging as Claude skills. A task shape is a repeatable input→output transformation — "session notes → build prompt", "product batch → marketplace listing", "raw CSV → formatted table" — not a topic. The run produces a scored backlog of skill candidates, deduped against everything already installed, plus upload-ready frontmatter drafts for the top five.

This skill reads history and reports. It writes no files, writes no memory, and installs nothing.

## Triggers

Run this workflow when the user says any of:

- `run skill prospector`
- `what skills should I build`
- `skill backlog`
- `find skill candidates`

or otherwise asks which recurring chores in their chat history deserve automation.

## Preconditions

- Past-chats tools available: `conversation_search` and `recent_chats`. If either is missing, say so and stop — there is no other qualifying evidence source.
- `view` access to `/mnt/skills` for the dedupe pass.
- History scope matches intent. Inside a Project only that Project's chats are searchable; outside, only non-Project chats. State the active scope in the report.
- Recurrence window defaults to 30 days; the user may override before the run starts.

## Generic probes

Fixed list. Run one `conversation_search` per probe, verbatim. `conversation_search` is a literal keyword match, so short literal task phrases outperform clever queries — do not elaborate or combine them.

| # | Probe |
|---|---|
| 1 | write a prompt |
| 2 | build prompt |
| 3 | convert this |
| 4 | reformat |
| 5 | summarize this |
| 6 | draft a |
| 7 | generate |
| 8 | make a table |
| 9 | turn this into |
| 10 | same as before |
| 11 | like last time |
| 12 | another one |
| 13 | checklist |
| 14 | package this |

## Seed derivation rule

derive 5–10 domain seeds fresh each run — (a) short project/topic nouns from the current in-context userMemories, weighting "top of mind" items over background history; (b) recurring content nouns from the `recent_chats` titles gathered in the window step. Show the derived seed list to the user for a one-line veto before sweeping (reply `go` to accept, or strike names). Never carry seeds from this SKILL.md, from a prior run, or from memory alone — a project's presence in memory does not prove it is active, and sweeping dead projects wastes the run.

Seeds are disposable per-run inputs. They earn no scoring bonus and no exemption from the recurrence gate.

## Workflow

Execute in order. Gates must bite — do not proceed past a failed gate.

1. **Window.** Establish the coverage window (default 30 days). Page `recent_chats` newest-first: `n=20`, `sort_order='desc'`, then repeat with `before` set to the earliest `updated_at` seen so far, at most 5 calls total. Stop early once results pass the window start. Record coverage `FULL` (window fully paged within the cap) or `SAMPLED` (cap hit first). Collect every chat title seen — they feed seed derivation.

2. **Derive seeds.** Apply the Seed derivation rule above. GATE: the seed list has been shown to the user and accepted (`go`) or edited (struck names removed) before any seed search runs. Generic probes need no approval and may run before the veto reply arrives.

3. **Probe sweep.** Run one `conversation_search` per generic probe and per accepted seed, `max_results=10`. Dedupe hits by chat url. Group deduped hits into task shapes — a shape is a repeatable input→output transformation ("campaign brief → ad variants"), never a topic ("wrote about marketing"). Classify from snippet content, not titles alone.

4. **Recurrence gate.** A candidate is a shape appearing in ≥3 distinct chats within the window. EXPECT: every candidate row lists ≥3 chat urls as evidence. Shapes at 1–2 occurrences go to the watch list, not the backlog. Being a seed grants no exemption — seeds are disposable per-run inputs, and recurrence evidence is still required.

5. **Score.** For each candidate compute `score = freq × est_minutes_per_occurrence × automatability(1–5)`. `freq` = distinct chats in the window. Estimate minutes conservatively from snippet context — what the manual version of the task costs each time — and state the estimate basis in a note column. Sort descending.

6. **Dedupe.** `view /mnt/skills` and walk all subtrees present (`public`, `examples`, `plugins`, `user`). Compare each candidate against installed skill names and descriptions. Label every candidate `NEW`, `DUPLICATE (existing skill name)`, or `EXTEND (existing skill name + gap)` — for `EXTEND`, name the gap. GATE: no candidate carries a `NEW` label until the dedupe pass has completed over the full tree.

7. **Draft top 5.** For each of the five highest-scoring `NEW` or `EXTEND` candidates, produce:
   - proposed `name` — lowercase-hyphen, valid as a directory name;
   - `description` — ≤200 characters, third person, written pushy: what the skill does plus explicit when-to-use trigger phrases. Skills trigger on the frontmatter description alone, so it carries the entire triggering load;
   - a 3-step workflow outline;
   - inputs → outputs;
   - a one-line build-prompt seed: "Build a Claude skill named X that …".
   Scope every draft standalone — skills cannot invoke other skills, so no draft may depend on another skill existing.

8. **Report.** Emit, in order: backlog table `rank | shape | freq | est min | auto | score | dedupe | chats`; the top-5 draft blocks; the watch list; the seed list actually used (accepted and struck names noted); the coverage line (window dates, `FULL` or `SAMPLED`, active scope). No memory writes, no file writes.

## Scoring rubric

`score = freq × est_minutes × automatability`

Automatability anchors:

| Score | Anchor |
|---|---|
| 1 | judgment-heavy — output turns on taste or per-case negotiation; a skill could at best scaffold |
| 2 | mostly judgment inside a mechanical shell — a template exists, but content is bespoke each time |
| 3 | mixed — stable structure, variable content needing moderate adaptation |
| 4 | near-mechanical — fixed transformation with light per-run parameters |
| 5 | fully mechanical — deterministic input→output, same steps every time |

Round minute estimates down when unsure and say why in the note column: an inflated backlog erodes trust in the whole report.

## Draft template

```
### <rank>. <proposed-name>  —  score <score>
description (<chars>/200): <description with trigger phrases>
workflow: 1) <step> 2) <step> 3) <step>
inputs: <inputs> → outputs: <outputs>
build seed: Build a Claude skill named <proposed-name> that <one line>
```

## Edge cases

- **Seed with zero hits:** report it in the seed list as swept, 0 hits. It produces no candidate and no watch entry — memory naming a project is not evidence the project is active.
- **Shape spanning generic and seed hits:** merge into one shape; count each distinct chat once.
- **`SAMPLED` coverage:** flag it prominently. Scores are lower bounds; a 2-hit near-miss under `SAMPLED` deserves a watch-list note that coverage may be the cause.
- **User strikes every seed:** run generic probes only; note "seeds: all struck" in the report.
- **More than 5 `NEW`/`EXTEND` candidates:** draft the top 5 only; the rest remain backlog rows.
- **`DUPLICATE` ranks in the top 5:** skip it for drafting, point to the installed skill, and pull up the next candidate.

## Guardrails

- Counts reported as observed within the window; never extrapolate to all-time frequency.
- A candidate never enters the backlog on memory evidence alone — chat-history recurrence within the window is the only qualifying evidence.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- If zero candidates clear the ≥3 gate: say so, show the watch list, stop.

## Surfaces

- **No past-chats tools in this environment (e.g. Claude Code)?** Run this skill's sweep over a conversations export instead: same lexicon, thresholds, gates, and output format; per-call search budgets don't apply. `scripts/cc_history_export.py` (bundled in this plugin) produces the export from local Claude Code history. See `docs/surfaces.md`.
- **Dedupe locations:** `/mnt/skills` on claude.ai. Elsewhere scan `~/.claude/plugins/cache` plus any project-level `.claude/skills/`.
