# Rule Arbitration Prompt (v2.1)

Phase 3 of a cleanup cycle. Runs **after** the five rule generators — `rule-drift`,
`claim-audit`, `ambiguity-preempt`, `friction-audit`, `praise-miner` — and
**before** `memory-gc`.

Two ways to run it:

- **claude.ai app:** fill the `<<< >>>` blocks below, paste the whole prompt into a
  fresh chat in the same scope as your rule set (outside any Project for global
  memory).
- **Claude Code:** `/brainrot:arbitrate <cycle-dir>` reads the same inputs from
  files and writes the output blocks as files. See `commands/arbitrate.md`.

The "K-list" is your canonical numbered rules list (`K1…Kn`) — the standing rules
you keep in persistent memory, numbered so verdicts and merges can reference lines.

Pipeline note: skip the per-skill staging steps (`stage rules` / `stage fixes`)
when running a full cycle. The cycle's single write happens in `memory-gc`, fed by
the SELECTED block here — per-skill staging would double-write.

---

## PROMPT — copy from here

You are running **rule arbitration**. This is a read-and-decide operation. You do
not write memory, you do not call `memory_user_edits` (or edit any memory file),
and you do not modify anything unless I explicitly approve the final selection.
You do not search chat history — not to verify evidence, not to backfill missing
fields, not to rebuild a pool. Verification happened upstream in the skills and
happens downstream in `memory-gc`; you arbitrate the pasted material exactly as
given. `memory-gc` performs the single write later; your job is to hand it a
defensible, budget-fitted set.

Trigger discipline: act on this only because I pasted this prompt (or invoked the
arbitrate command). Do not infer an arbitration run from any other phrasing in
this conversation.

### INPUTS

Paste full skill reports, not extracted rule lines — incident counts, refs, and
provenance come from the report bodies.

Current canonical K-list (verbatim, numbered):

<<< PASTE K-LIST >>>

`rule-drift` verdict table (KEEP / REINFORCE / REWRITE / RETIRE, with drafts).
Mark each RETIRE **confirmed** or **pending** — `rule-drift` gates retirement on
per-rule confirmation, and the arithmetic treats the two differently:

<<< PASTE RULE-DRIFT VERDICTS >>>

`claim-audit` report (incident log + prevention lines):

<<< PASTE CLAIM-AUDIT REPORT >>>

`ambiguity-preempt` report (incidents table + drafted rules):

<<< PASTE AMBIGUITY-PREEMPT REPORT >>>

`friction-audit` report (ranked patterns + remediation table). Only `MEMORY-EDIT`
remediations enter the pool; `SKILL-CANDIDATE` and `PROMPT-PATTERN` items are out
of scope here and pass through to HANDOFF as non-memory follow-ups:

<<< PASTE FRICTION-AUDIT REPORT >>>

`praise-miner` report (CLEAN/MIXED table + do-more rules):

<<< PASTE PRAISE-MINER REPORT >>>

Backlog carried from the previous cycle (the BACKLOG block of the last run, or
`NONE` on a first cycle):

<<< PASTE PRIOR BACKLOG or NONE >>>

Permanent exclusions (topics or rules you have permanently banned from canon —
one per line, each a name plus an optional one-line fingerprint; or `NONE`):

<<< PASTE PERMANENT-EXCLUSION LIST or NONE >>>

Parameters (defaults apply if I leave them blank):

- Analysis window: <<< e.g. 30 days, ending YYYY-MM-DD >>>
- Memory hard cap: 30 lines
- Post-GC target: 20 lines
- Selection threshold: score ≥ 12
- Backlog floor: score ≥ 6

Sanity before anything else: backlog floor < threshold ≤ 21; post-GC target ≤
hard cap; the window has an explicit end date. A failed check stops the run.

A skill reporting zero findings is a valid input — proceed without that pool and
say so in HANDOFF. A blank block or an untouched placeholder is not: say so and
stop. Do not reconstruct a missing pool from chat history and do not pad a thin
one — a pool assembled by a different method is not comparable to one produced by
its skill. If a source ran on a different window than the one above, its
incidents still count, but flag the mismatch in HANDOFF.

### STEP 0 — Baseline

`rule-drift` verdicts adjust the baseline; they are not pool records and are
never scored.

- Map `rule-drift`'s R-numbering onto the K-numbering by matching rule text. Flag
  any rule that maps to nothing or to two lines.
- Apply REINFORCE and REWRITE replacement lines to the working K-list.
- Confirmed RETIREs leave the working K-list. Pending RETIREs stay but are
  marked — their lines are contingent headroom until I rule at the veto gate.

### STEP 1 — Normalize

Convert every proposal into one record:

| field | value |
|---|---|
| `id` | `CA-01…`, `AP-01…`, `FA-01…`, `PM-01…` by source, `BL-01…` for carried backlog, in input order |
| `source` | originating skill, or `backlog` |
| `rule` | the proposed rule, verbatim as received |
| `evidence` | `STRONG` / `PROVENANCE-WEAK` / `PROPOSED` |
| `incidents` | count of distinct supporting incidents inside the analysis window |
| `newest` | date of the most recent supporting incident; `≤window` when the source gives counts but not dates |
| `refs` | source links or chat titles |

Evidence tiers, applied strictly:

- **STRONG** — the source's log attests the supporting incidents as confirmed
  user-turn corrections, commitments, or preferences (the mining skills enforce
  `Human:`-attribution before logging; their attested incidents qualify even
  though they paraphrase). Praise-miner records qualify via attested `CLEAN`
  chats — but see the Step 4 cost rule.
- **PROVENANCE-WEAK** — the source itself marks the support as summary-derived,
  attribution-unconfirmed, or otherwise unverified (`MIXED` praise chats count
  here at their half weight).
- **PROPOSED** — originated as an assistant recommendation with no Human uptake.
  A positive Human reaction is not uptake. Only an explicit Human commitment is.

A skill-drafted rule grounded in confirmed corrections tiers by its incidents,
not by who worded the rule — `PROPOSED` marks rules whose only support is an
assistant suggestion. If a record's tier is ambiguous, assign the lower tier and
note it. Do not upgrade a tier to make a rule survive.

Carried backlog records enter with the tier, slug, and score recorded last cycle.

### STEP 2 — Hard gates (before scoring)

Reject with reason codes. A record can trip several gates — report every code it
trips, still one line.

- `R-PROPOSED` — evidence tier is `PROPOSED`.
- `R-EXCLUDED` — the rule names, matches, or re-derives an entry on the
  permanent-exclusion list. Not overridable in this run; if the list is `NONE`,
  the gate is inert.
- `R-COVERED` — the behavior is already fully required or forbidden by a K-line
  that survives Step 0. Cite the covering `Kn`. Full coverage only — partial
  overlap is Step 5 merge material, not a rejection.
- `R-UNAUDITABLE` — the rule has no observable violation. If `rule-drift` could
  not score adherence to it next cycle, it is a sentiment, not a rule. Reject;
  where an obvious concrete form exists, append a one-line suggested rewrite to
  the REJECTED entry for the source skill's next run. The suggestion does not
  re-enter this run.
- `R-STALE` — newest supporting incident falls outside the analysis window.
  Exemption: a carried record marked `next-cycle-priority` skips this gate
  exactly once.

Not a rejection: a rule carrying an unfilled placeholder (`DEFAULT NEEDED — user
to fill`) is flagged `NEEDS-VALUE` and continues, but cannot be SELECTED unless I
supply the value at the veto gate.

### STEP 3 — Cluster

Group survivors that address the same underlying behavior even when worded
differently across skills. Per cluster:

- an id `CL-01…` and a **slug** — a short kebab-case name for the behavior
  (`search-before-version-claims`), stable across rewordings. Reuse the prior
  cycle's slug when a cluster matches a carried record; otherwise coin one.
- one **merged rule** in my voice.
- the **highest** member evidence tier and the **union** of in-window incidents.

Overlap across the mining skills is expected — a cluster of three is one rule
with strong support, not three rules. A prevention rule and a do-more rule about
the same behavior (stop doing X / keep doing not-X) are one cluster, merged as
the prevention form. Membership is reported in AUDIT, never asserted silently.

### STEP 4 — Score

For each cluster:

- `E` = 1.0 if `STRONG`, 0.5 if `PROVENANCE-WEAK`
- `R` = distinct in-window incident count, capped at 5
- `C` = cost of a violation: 1 minor rework, 2 lost work or wrong artifact
  shipped, 3 security, data loss, or credential exposure. `C = 3` must name the
  incident that demonstrates the exposure. **Do-more rules score `C = 1` by
  definition** — failing to repeat a liked pattern is minor rework at worst; they
  earn selection through `R` and `F`. (Consequence, intended: a do-more rule
  needs 4–5 distinct `CLEAN` chats to clear the default threshold.)
- `F` = 1 if any incident falls in the most recent third of the window. Derive
  from the source's recency markers when it gives no dates; unknowable → 0.

**Score = E × (2R + 3C + 2F)** — maximum 21. Show `E R C F` per cluster in
AUDIT; a bare score is not auditable.

Built-in consequence, intended: with `E = 0.5` the ceiling is 10.5, so at the
default threshold a `PROVENANCE-WEAK` cluster can reach BACKLOG but never
SELECTED. Weak-provenance rules enter canon only after recurring with strong
evidence.

A carried `next-cycle-priority` record keeps last cycle's score unless this
cycle's evidence changes it.

Tie-break in order: prevents a class over prevents an instance → higher `C` →
shorter rule text → more recent.

### STEP 5 — Budget

Compute and show the arithmetic:

```
current K-lines
− confirmed rule-drift retirements
+ rewrites that add lines (usually 0)
= post-retirement count

firm headroom       = post-GC target − post-retirement count
contingent headroom = firm + pending retirements (resolved at the veto gate)
```

Then check for **zero-cost merges**: any cluster whose intent folds into a
K-line that survives Step 0 by rewording that line rather than adding one. These
consume no headroom and are preferred wherever the merged line stays legible.
Propose the exact rewritten K-line text. Never merge into a retired or
pending-retire line.

If firm headroom is 0 or negative, say so plainly. Do not shrink rule text to
smuggle extra rules onto one line, and do not propose exceeding the hard cap.
Headroom is provisional until conflicts and pending retirements are ruled on —
recompute after my decisions.

### STEP 6 — Conflicts

Flag, do not resolve:

- a cluster contradicting a surviving K-line;
- two clusters contradicting each other;
- **revenants** — a cluster substantially restating a K-line retired this cycle.
  Retire-then-re-add is a signal for my attention, not a silent add.

Present each as: the two texts, what each implies in one concrete situation, and
which is better supported. I decide at the veto gate. A cluster party to an
unresolved conflict cannot be SELECTED — it holds at `HOLD-CONFLICT`.

### STEP 7 — Select

- Score ≥ threshold, fits firm headroom, no unresolved conflict, no unfilled
  placeholder → **SELECTED**
- Score ≥ threshold but conflicted → **HOLD-CONFLICT**
- Score ≥ threshold but no headroom → **BACKLOG**, marked `next-cycle-priority`:
  first claim on next cycle's headroom, carries its score, R-STALE-exempt once.
  A second cycle with no fresh evidence drops it to ordinary backlog.
- Backlog floor ≤ score < threshold → **BACKLOG**
- Score < backlog floor → **REJECTED**, code `R-LOWSCORE`

Selected rules must each be: one line, imperative, self-contained, free of
unfilled placeholders, and free of project names or paths that will go stale
before the next cycle.

### STEP 8 — Output

Produce five blocks, in this order, nothing else:

**A. AUDIT** — one table: `CL-id | slug | members | tier | E R C F | score |
disposition`, headed by each source's coverage line (`FULL`/`SAMPLED`), followed
by one short block per unresolved conflict (the two texts, implication, support).
Cluster membership and score components live here.

**B. SELECTED** — formatted as `memory-gc` edit-plan rows so it pastes there
without editing: `op (add/replace) | K-line (— for adds) | new text | reason
(CL-id · slug · score) | evidence (refs)`. A `MERGE-INTO-Kn` is a `replace` on
`Kn` carrying the reworded line.

**C. BACKLOG** — ranked: `CL-id | slug | score | tier | re-entry criterion`
(what would have to recur to clear threshold next cycle). Write to a
downloadable file when the environment allows; otherwise emit one fenced block.
Either way it must paste cleanly into the next run's prior-backlog input.

**D. REJECTED** — `id | rule | code(s)`, one line each, plus the suggested
rewrite where `R-UNAUDITABLE` produced one. No elaboration.

**E. HANDOFF** — 7 lines max: counts per bucket; firm/contingent headroom
result; unresolved-conflict and pending-retirement counts; non-memory follow-ups
passed through from `friction-audit`; any window mismatch; the reminder to carry
the BACKLOG block into the next cycle; the exact next command. This feeds
`handoff-distill`.

### STEP 9 — Veto gate

Stop after the five blocks. Ask me to rule **by CL-id**: approve, amend, or veto
each SELECTED row; resolve each conflict and pending retirement; fill or defer
each `NEEDS-VALUE`. Nothing proceeds to `memory-gc` until I answer. If I veto a
cluster, do not silently promote the next backlog item into its headroom — show
me the vacancy and let me fill it. After my rulings, re-emit final **B** and
**E** reflecting them; that final B, not the pre-veto version, is what feeds
`memory-gc`.

## PROMPT — copy to here

---

## Changelog

**v2 → v2.1** — added the `praise-miner` pool (`PM-` records; do-more rules score
`C = 1`; a prevention rule and its do-more mirror cluster together); replaced the
hardcoded exclusion rule with the parameterized permanent-exclusion list and gate
`R-EXCLUDED`; generalized the K-list definition; documented the file-mode command
form (`/brainrot:arbitrate`).

**v1 → v2** — inputs became full skill reports; `friction-audit` scoped to
`MEMORY-EDIT` remediations; STEP 0 baseline (R→K reconciliation, confirmed vs
pending RETIREs, firm vs contingent headroom); backlog round-trip with
`next-cycle-priority` mechanics; gates `R-COVERED` and `NEEDS-VALUE`; revenant
check and `HOLD-CONFLICT`; auditable scoring (`E R C F` shown, in-window
counting, weak-provenance ceiling stated); collision-free ids and slugs; SELECTED
emitted as `memory-gc` edit-plan rows; explicit no-history-search rule; parameter
sanity checks.

## Cycle notes

Log per run so the next cycle can compare:

| date | proposals in | carried | clusters | selected | headroom | conflicts | notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
