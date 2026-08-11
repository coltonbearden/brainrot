---
description: Show where you are in a brainrot cleanup cycle and the exact next step
argument-hint: [cycle-dir]
---

Guide the user through a brainrot cleanup cycle.

First, locate this plugin's installed root (the directory that contains this
command's parent `commands/` folder) and read `docs/runbook.md` there — it
defines the six phases (0–5), the ordering rationale, and which skill runs in
each phase.

If `$ARGUMENTS` names a cycle directory, inspect it: which of the phase report
files already exist (`rule-drift.md`, `claim-audit.md`, `ambiguity-preempt.md`,
`friction-audit.md`, `praise-miner.md`, `audit.md`/`selected.md` from
arbitration, and any retro or ledger files)? From what exists, state plainly:

1. which phase the cycle is in,
2. the single exact next action — the skill to run and where its output file
   goes, or `/brainrot:arbitrate <cycle-dir>` when all five generator reports
   are present, or `memory-gc` when a post-veto `selected.md` exists,
3. anything out of order (e.g. generator reports present but no `rule-drift.md`
   — Phase 1 must precede Phase 2, per the runbook's budget rationale).

If no cycle directory is given, propose creating one (a dated folder such as
`./brainrot-cycle-YYYY-MM/`), list the eight input files it will accumulate, and
name Phase 0's first action.

Keep the reply short: current phase, next action, at most one warning. Do not
run any skill from here — this command orients; the user launches each phase.
