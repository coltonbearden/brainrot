# BUILD PROMPT 06 — `ambiguity-preempt` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `ambiguity-preempt`: find clarify-loops and wrong-guess-then-corrected sequences in chat history, cluster them by ambiguity axis, and draft standing disambiguation rules (default + inline-statement + ask-only-if-destructive), memory-paste-ready, with optional gated staging. Deliver `/mnt/user-data/outputs/ambiguity-preempt.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `ambiguity-preempt` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤300), UTF-8, LF, no placeholders |
| Package | zip with `ambiguity-preempt/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `conversation_search` is literal keyword match | One search per lexicon term; short literal phrases |
| `recent_chats` caps at 20/call | Window default 30d; `SAMPLED` label if uncovered |
| `memory_user_edits` cap 30 | Rules condensed to ≤1 dense line per axis; staging behind confirm gate |
| Axis seeds are user-specific and drift | Axis table marked TUNABLE; skill re-derives instances from userMemories at runtime when present |
| Project chats invisible from outside Projects | State: run outside Projects for global audit |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: ambiguity-preempt
description: Finds clarify-loops and wrong guesses in chat history, clusters ambiguity axes, drafts standing disambiguation rules. Use for run ambiguity audit, disambiguation rules, stop asking which.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run ambiguity audit` · `disambiguation rules` · `stop asking which` · `ambiguity preempt`

### 4.3 Embedded lexicon (verbatim table; tunable)
| Clarify-loop terms | Wrong-guess terms |
|---|---|
| which one | not that one |
| which machine | the other one |
| which account | other account |
| which repo | other machine |
| which folder | wrong repo |
| which version | wrong machine |
| did you mean | wrong folder |
| do you mean | meant the other |
| clarify | — |

### 4.4 Axis table (verbatim; header TUNABLE — instances below are seeds, re-derive from userMemories at runtime)
| Axis | Seed instances |
|---|---|
| MACHINE | laptop vs desktop vs remote dev box |
| ACCOUNT | work vs personal account on the same service |
| REPO/PROJECT | active project set |
| PATH | canonical projects root vs deprecated roots |
| SHELL/ENV | bash vs zsh vs PowerShell |
| SURFACE | claude.ai vs Claude Code vs Claude Desktop |
| OTHER | anything recurring outside the above |

### 4.5 Rule form (verbatim — every drafted rule must match)
`When <axis> is unspecified, default to <value>; state the chosen default inline in the response; ask only if the action is destructive or irreversible.`

### 4.6 Workflow to encode (imperative, numbered, gated)
1. **Window.** Default 30d via `recent_chats` recipe (desc, n=20, `before` pagination, ≤5 calls). Record coverage `FULL|SAMPLED`.
2. **Sweep.** One `conversation_search` per lexicon term, `max_results=10`. Dedupe by chat url. Classify each hit `CLARIFY-LOOP` (assistant asked) or `WRONG-GUESS` (assistant guessed, user corrected) from the snippet; unclear → one `read_conversation` open (hit `page_token`, ≤2 per axis) or discard.
3. **Cluster.** Assign each incident an axis. Incidents table: `axis | type | count | example (paraphrase) | chats`.
4. **Threshold.** Draft a rule only for axes with ≥2 incidents. EXPECT: every drafted rule cites ≥2 incident chats. Single-incident axes → watch list.
5. **Draft.** One rule per qualifying axis in the §4.5 form. Default values: take from userMemories where an explicit canonical exists; otherwise from the most frequent corrected-to value in incidents; otherwise mark `DEFAULT NEEDED — user to fill` and exclude from staging.
6. **Condense.** Rules table + a single memory-paste block, ≤1 dense line per axis, total ≤6 lines.
7. **Optional staging.** Only on `stage rules`: `memory_user_edits view` → E0 → plan with expected E1 → explicit confirm → execute → re-view, GATE observed == E1. Rules containing `DEFAULT NEEDED` are never staged.
8. **Report.** Incidents table + rules table + paste block + watch list + coverage line.

### 4.7 Guardrails (verbatim)
- Never invent a default the evidence doesn't support — `DEFAULT NEEDED` is the honest cell.
- A drafted default never overrides an explicit user instruction in a live conversation.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- Zero qualifying axes → report cleanly, stop.

### 4.8 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Lexicon → Axis table → Rule form → Workflow → Output template → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/ambiguity-preempt/SKILL.md` | §4.1 + body per §4.2–4.8 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/ambiguity-preempt
# write SKILL.md per §4
wc -l < /home/claude/ambiguity-preempt/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/ambiguity-preempt/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*ambiguity-preempt\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['DEFAULT NEEDED', 'destructive or irreversible', 'WRONG-GUESS']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run ambiguity audit" /home/claude/ambiguity-preempt/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/ambiguity-preempt.zip ambiguity-preempt
unzip -l /mnt/user-data/outputs/ambiguity-preempt.zip                   # EXPECT: ambiguity-preempt/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate one axis with 3 incidents and a clear corrected-to value (→ rule drafted) and one with a single incident (→ watch list). Fix if the gates don't bite.

## 7. Deliver
Present `/mnt/user-data/outputs/ambiguity-preempt.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run ambiguity audit`; (c) D# deviations if any. Nothing else.
