---
name: arbitrate
description: Arbitrate a cleanup cycle's rule proposals into a budget-fitted, evidence-gated selection for memory-gc (file mode)
argument-hint: <cycle-dir>
disable-model-invocation: true
---

Run **rule arbitration** in file mode over the cycle directory given in
`$ARGUMENTS`.

First, locate this plugin's installed root (the directory whose `skills/`
folder contains this skill) and read `docs/arbitrate-prompt.md` there.
That file is the authoritative procedure — every step, gate, scoring rule, and
output block defined between its "PROMPT — copy from here" and "copy to here"
markers applies verbatim, with only the input/output substitutions below.

**Input substitutions.** Instead of pasted `<<< >>>` blocks, read these files
from the cycle directory (`$ARGUMENTS`):

| paste block | file |
|---|---|
| K-list | `k-list.md` |
| rule-drift verdicts | `rule-drift.md` |
| claim-audit report | `claim-audit.md` |
| ambiguity-preempt report | `ambiguity-preempt.md` |
| friction-audit report | `friction-audit.md` |
| praise-miner report | `praise-miner.md` |
| prior backlog | `backlog-prior.md` (`NONE` on a first cycle) |
| permanent exclusions + parameters | `params.md` |

A missing file is the file-mode equivalent of an untouched placeholder: name it
and stop — do not substitute chat history, memory, or guesses. A file containing
only `NONE` is a valid empty input. `params.md` holds the analysis window, caps,
threshold, floor, and the permanent-exclusion list; defaults from the procedure
apply to anything it omits.

**Output substitutions.** Write the five output blocks as files in the cycle
directory — `audit.md`, `selected.md`, `backlog.md`, `rejected.md`,
`handoff.md` — then print a one-line pointer to each. `backlog.md` doubles as
the next cycle's `backlog-prior.md`.

**The veto gate is unchanged and interactive.** After writing the five files,
stop and ask the user to rule by CL-id exactly as the procedure specifies.
Nothing is final until they answer; after their rulings, rewrite `selected.md`
and `handoff.md` to reflect them. This skill never edits memory, `CLAUDE.md`,
or any file outside the cycle directory — `memory-gc` performs the cycle's
single write later, from the post-veto `selected.md`.

Try the plugin's `fixtures/example-cycle/` directory for a worked example of the
input format.
