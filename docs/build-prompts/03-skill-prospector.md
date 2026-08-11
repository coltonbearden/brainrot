# BUILD PROMPT 03 — `skill-prospector` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. Do not ask clarifying questions — every decision is pre-made here. Deliver the complete skill in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read it for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `skill-prospector`: detect task shapes recurring across chat history, score them as skill candidates, dedupe against installed skills, and draft upload-ready frontmatter for the top candidates. Deliver `/mnt/user-data/outputs/skill-prospector.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `skill-prospector` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤300), UTF-8, LF, no placeholders |
| Package | zip with `skill-prospector/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| Installed skills are enumerable at `/mnt/skills/` (public, examples, plugins, user) | Dedupe step = `view /mnt/skills` tree, compare names + descriptions |
| claude.ai skills cannot invoke other skills | Every candidate must be scoped standalone |
| Candidate descriptions must fit claude.ai upload limits | Drafts: lowercase-hyphen names, ≤200-char descriptions |
| `conversation_search` is literal keyword match | Probe list = short literal task phrases, one search each |
| `recent_chats` caps at 20/call | Recurrence window default 30d, `SAMPLED` label if uncovered |
| Persistent memory can describe projects that are no longer active | Domain seeds are NEVER hardcoded — derived fresh each run and vetoed by the user (§4.3) |
| Skills trigger on frontmatter description | Drafts written "pushy": what it does + explicit when-to-use phrases |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: skill-prospector
description: Finds recurring tasks in chat history worth converting into skills. Use for run skill prospector, what skills should I build, skill backlog. Scores candidates, drafts upload-ready descriptions.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run skill prospector` · `what skills should I build` · `skill backlog` · `find skill candidates`

### 4.3 Probes (generic list verbatim; domain seeds derived at run time — never hardcoded)
| Generic probes (fixed, one search each) |
|---|
| write a prompt |
| build prompt |
| convert this |
| reformat |
| summarize this |
| draft a |
| generate |
| make a table |
| turn this into |
| same as before |
| like last time |
| another one |
| checklist |
| package this |

**Domain-seed derivation rule (verbatim in SKILL.md):** derive 5–10 domain seeds fresh each run — (a) short project/topic nouns from the current in-context userMemories, weighting "top of mind" items over background history; (b) recurring content nouns from the `recent_chats` titles gathered in the window step. Show the derived seed list to the user for a one-line veto before sweeping (reply `go` to accept, or strike names). Never carry seeds from this SKILL.md, from a prior run, or from memory alone — a project's presence in memory does not prove it is active, and sweeping dead projects wastes the run.

### 4.4 Workflow to encode (imperative, numbered, gated)
1. **Window.** Default 30d via `recent_chats` pagination (desc, n=20, `before` = earliest `updated_at`, ≤5 calls). Record coverage `FULL|SAMPLED` and collect all chat titles for seed derivation.
2. **Derive seeds.** Apply the §4.3 derivation rule. GATE: seed list shown and user-accepted (or struck) before any seed search runs. Generic probes need no approval.
3. **Probe sweep.** One `conversation_search` per generic probe and per accepted seed, `max_results=10`. Dedupe hits by chat url. Group hits into task shapes (a shape = a repeatable input→output transformation, e.g. "session → build prompt", "product batch → marketplace listing").
4. **Recurrence gate.** Candidate = shape appearing in ≥3 distinct chats. EXPECT: every candidate row lists ≥3 chat urls. Below threshold → "watch" list, not the backlog. Being a seed grants no exemption — seeds are disposable per-run inputs, and recurrence evidence is still required.
5. **Score.** `score = freq × est_minutes_per_occurrence × automatability(1–5)`. Estimate minutes conservatively from snippet context; state the estimate basis in a note column. Sort descending.
6. **Dedupe.** `view /mnt/skills` (all subtrees present). Mark each candidate `NEW` / `DUPLICATE (existing skill name)` / `EXTEND (existing skill name + gap)`. GATE: no `NEW` label without the dedupe pass completing.
7. **Draft top 5.** For each: proposed `name` (lowercase-hyphen), `description` ≤200 chars (pushy: capability + trigger phrases), 3-step workflow outline, inputs/outputs, and a one-line build-prompt seed ("Build a claude.ai skill named X that …").
8. **Report.** Backlog table `rank | shape | freq | est min | auto | score | dedupe | chats` + top-5 draft blocks + watch list + seed list used + coverage line. No memory writes, no file writes.

### 4.5 Guardrails (verbatim)
- Counts reported as observed within the window; never extrapolate to all-time frequency.
- A candidate never enters the backlog on memory evidence alone — chat-history recurrence within the window is the only qualifying evidence.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- If zero candidates clear the ≥3 gate: say so, show the watch list, stop.

### 4.6 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Generic probes → Seed derivation rule → Workflow → Scoring rubric (automatability anchors 1=judgment-heavy … 5=fully mechanical) → Draft template → Edge cases → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/skill-prospector/SKILL.md` | §4.1 + body per §4.2–4.6 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/skill-prospector
# write SKILL.md per §4
wc -l < /home/claude/skill-prospector/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/skill-prospector/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*skill-prospector\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['≥3', '/mnt/skills', 'automatability', 'derive 5–10 domain seeds fresh each run', 'presence in memory does not prove it is active']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run skill prospector" /home/claude/skill-prospector/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/skill-prospector.zip skill-prospector
unzip -l /mnt/user-data/outputs/skill-prospector.zip                    # EXPECT: skill-prospector/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate a run where memory names a project with zero chat hits in the window (→ seed derived, swept, no candidate — must NOT enter the backlog) and a shape at 4 recurrences (→ backlog with draft). Also simulate one at 2 recurrences (→ watch list). Fix the skill if any gate fails to bite.

## 7. Deliver
Present `/mnt/user-data/outputs/skill-prospector.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run skill prospector`; (c) D# deviations if any. Nothing else.
