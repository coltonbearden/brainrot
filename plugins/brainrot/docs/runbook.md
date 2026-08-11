# The cleanup cycle

For a full cleanup, the ordering constraint that matters most isn't "cheap to
expensive" — it's that five of these skills all produce standing rules, and
persistent memory has a hard line cap (30 on the claude.ai ledger) that is
usually mostly spent. If you run the generators before the auditors, you'll blow
the budget and be arbitrating under pressure. The sequence below runs auditors
first, mines second, arbitrates deliberately, and writes exactly once.

Pin one analysis window (30 days is the default) and reuse it in every phase so
findings are comparable and dedupe actually works.

## Phase 0 — Baseline

**usage-retro** (30-day, not 7). This is your before-picture, and it tells you
whether the corpus even has enough correction volume for the mining skills to
produce signal.

## Phase 1 — Ground truth, read-only

**decision-ledger**, then **rule-drift**.

The ledger becomes your authority for what's actually open — memory *asserts*
that items are open or decided; the ledger confirms status with provenance.
rule-drift has to run here, before anything generates new rules: freshly minted
rules have zero adherence history, so auditing them is meaningless, and
rule-drift's retire/rewrite verdicts are precisely what frees up line budget for
Phase 2's output. It also gives you a compliance check on any permanent-exclusion
rules you keep.

## Phase 2 — Mine corrections and successes, narrow → broad

**claim-audit** → **ambiguity-preempt** → **friction-audit**, then
**praise-miner**.

The first three mine the same underlying correction events. Narrow-first means
each broader pass reports only the residual the specialists didn't catch;
broad-first gets you three competing fixes for one incident. Tell friction-audit
explicitly to exclude incidents already claimed upstream and report residual
patterns only.

**praise-miner** closes the phase from the opposite polarity: it sweeps for
praised outputs, clean-checks each thread for zero corrections, and codifies
antecedents that repeat across ≥2 CLEAN chats into do-more rules. It shares the
pinned window but none of the dedupe interplay — a CLEAN chat is zero-correction
by definition, so nothing it claims overlaps the correction chain, which also
makes it the natural one to peel into its own thread if Phase 2 context runs
tight. Its rules join the Phase 3 pool with the rest — and note praise is
evidence about what to repeat, not a user decision, so expect these to earn
lines through recurrence rather than severity.

## Phase 3 — Arbitrate (the step people skip)

Pool every proposed rule from Phases 1 and 2 and run the arbitration procedure:
`/brainrot:arbitrate <cycle-dir>` in Claude Code, or the paste-in prompt in
`docs/arbitrate-prompt.md` on the claude.ai app. It normalizes proposals, gates
out the unauditable and the excluded, clusters duplicates across skills, scores
by evidence × recurrence × cost, and fits the survivors to your real headroom.

The budget math is the point. Worked example: 19 lines used against a 20-line
post-GC target leaves about one line of headroom unless rule-drift retired
something — so most of what the generators produce goes to a backlog file, not
memory. Deciding that deliberately is much better than discovering it at write
time. Nothing proceeds past the arbitration veto gate without your explicit
per-cluster ruling.

## Phase 4 — Single write window

**memory-gc**, once, with the ledger and the post-veto arbitrated selection as
inputs. This is the only phase that mutates state. Running it first instead
would force a re-run after every generator.

## Phase 5 — Forward-looking

**skill-prospector**, then **handoff-distill**.

skill-prospector must come after memory-gc — its domain seeds derive from
current memory plus recent chat titles, so pre-GC it would seed from retired
entries. Post-GC it also gets friction-audit's ranked patterns, which are your
best skill candidates by definition. handoff-distill closes out, capturing the
arbitration decisions and the unwritten backlog.

## Two practical notes

Don't attempt all ten in one thread — the mining skills are read-heavy and
you'll run out of context mid-audit. Split at roughly Phase 1 / Phase 3 /
Phase 5 and run handoff-distill at each boundary, not just at the end.

And when decision-ledger surfaces open items where a delay actually costs
something, pull those out and execute them rather than filing them into a
cleanup backlog.

Re-run usage-retro in 30 days — correction rate is the one number that should
move if the new rules landed.
