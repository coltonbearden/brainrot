# BUILD PROMPT 08 — `rule-drift` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `rule-drift`: extract the user's standing rules from persistent memory, probe recent chats for violations of each, score adherence, and verdict every rule KEEP / REINFORCE / REWRITE / RETIRE with drafts, plus optional gated staging. Deliver `/mnt/user-data/outputs/rule-drift.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `rule-drift` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤320), UTF-8, LF, no placeholders |
| Package | zip with `rule-drift/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| Rules live in the in-context userMemories block, not a file | Extraction step parses memory at runtime; probe examples below are patterns, not the live rule set |
| `conversation_search` is literal keyword match | Probes = short phrases a violation would provoke from the user |
| `recent_chats` caps at 20/call | Window default 30d; `SAMPLED` label if uncovered |
| Some rules are undetectable via search | `detectable?` column is honest; undetectable rules get verdict `KEEP (unmeasured)` |
| `memory_user_edits` cap 30; destructive ops need confirm | RETIRE and REWRITE never execute without explicit user confirm |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: rule-drift
description: Audits Claude's adherence to the user's standing rules across recent chats. Use for run rule drift, rule compliance audit, audit my rules. Scores each rule, proposes keep, rewrite, or retire.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run rule drift` · `rule compliance audit` · `audit my rules` · `rule drift`

### 4.3 Probe-design patterns (verbatim table — examples showing how to derive probes; skill derives real probes from the live rule set at runtime)
| Rule archetype | Violation probes (what the user says when it's broken) |
|---|---|
| Absolute paths required | `full path` · `which folder` · `where exactly` |
| Single recommendation | `which option` · `pick one` · `too many options` |
| Minimal preamble | `get to the point` · `skip the intro` |
| Delegate multi-step work to a build prompt | `give me a prompt instead` · `should have been a prompt` |
| Reproduce full corrected artifacts | `resend the whole` · `full file please` |
| No assuming work is done | `I never ran` · `not done yet` · `that didn't happen` |

### 4.4 Workflow to encode (imperative, numbered, gated)
1. **Extract.** Parse the standing rules section of in-context userMemories into: `rule id | text (condensed) | detectable? (Y/N) | probes (2–3, derived per §4.3 patterns)`. GATE: every detectable rule has ≥2 probes before sweeping. If no memory block exists: say so and stop.
2. **Window.** Default 30d via `recent_chats` recipe (desc, n=20, `before` pagination, ≤5 calls). Record coverage `FULL|SAMPLED`.
3. **Sweep.** One `conversation_search` per probe, `max_results=5`. Dedupe by chat url. A hit counts as a violation only if the snippet shows the user correcting assistant behavior; unclear → one `read_conversation` open (hit `page_token`, ≤2 per rule) or discard.
4. **Score.** Adherence table: `rule | violations found | last seen | evidence (title+url)`. Undetectable rules: `unmeasured`.
5. **Verdict.** Per rule, exactly one: `KEEP` (0 violations, still relevant) · `REINFORCE` (violations found — draft strengthened wording) · `REWRITE` (rule unclear or partially obsolete — draft replacement) · `RETIRE` (zero relevance in window AND user confirms). Every REINFORCE/REWRITE ships the exact replacement line.
6. **Confirm + optional staging.** RETIRE requires explicit per-rule user confirmation regardless of staging. On `stage changes`: `memory_user_edits view` → E0 → plan with expected E1 → explicit confirm → execute → re-view, GATE observed == E1.
7. **Report.** Adherence table + verdict table with drafts + coverage line.

### 4.5 Guardrails (verbatim)
- Absence of violation evidence is not proof of compliance under `SAMPLED` coverage — say so in the report.
- Never RETIRE silently; never merge two rules without showing both originals.
- Drafted rewrites must preserve the rule's intent; intent changes are flagged `INTENT-CHANGE` for the user.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.

### 4.6 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Probe-design patterns → Workflow → Verdict definitions → Output template → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/rule-drift/SKILL.md` | §4.1 + body per §4.2–4.6 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/rule-drift
# write SKILL.md per §4
wc -l < /home/claude/rule-drift/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/rule-drift/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*rule-drift\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['REINFORCE', 'RETIRE', 'unmeasured', 'INTENT-CHANGE']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run rule drift" /home/claude/rule-drift/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/rule-drift.zip rule-drift
unzip -l /mnt/user-data/outputs/rule-drift.zip              # EXPECT: rule-drift/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate a 4-rule set — one clean (KEEP), one violated twice (REINFORCE + draft), one undetectable (KEEP unmeasured), one dead (RETIRE pending confirm). Fix if verdicts don't route correctly.

## 7. Deliver
Present `/mnt/user-data/outputs/rule-drift.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run rule drift`; (c) D# deviations if any. Nothing else.
