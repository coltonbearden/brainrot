# BUILD PROMPT 05 — `claim-audit` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `claim-audit`: locate facts Claude asserted that the user then corrected, root-cause each incident, and output a prevention ruleset (search-first triggers + verification gates) with optional gated memory staging. Deliver `/mnt/user-data/outputs/claim-audit.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `claim-audit` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤300), UTF-8, LF, no placeholders |
| Package | zip with `claim-audit/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `conversation_search` is literal keyword match | One search per lexicon term; content-noun phrasing |
| `recent_chats` caps at 20/call | Window default 30d; `SAMPLED` label if uncovered |
| Snippets may truncate mid-turn | Root-cause only after confirming the correction is in a human turn |
| `read_conversation` needs real id + hit `page_token` | ≤2 opens per incident; paraphrase evidence |
| `memory_user_edits` cap 30; destructive ops need confirm | Prevention rules staged only behind a confirm gate |
| Project chats invisible from outside Projects | State: run outside Projects for global audit |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: claim-audit
description: Finds facts Claude asserted then the user corrected. Use for run claim audit, hallucination audit, what did you get wrong. Root-causes incidents, outputs prevention and search-first rules.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run claim audit` · `hallucination audit` · `what did you get wrong` · `claim audit`

### 4.3 Embedded lexicon (verbatim table; tunable)
| Term (one search each) |
|---|
| actually it's |
| that's wrong |
| doesn't exist |
| no such |
| not a real |
| hallucinat |
| made that up |
| outdated |
| wrong version |
| deprecated |
| that flag |
| that API |
| invented |
| check again |

### 4.4 Incident schema + root-cause enum (verbatim)
Schema: `id | asserted claim (paraphrase) | correction (paraphrase) | domain | root cause | chat (title+url)`
Domains: `VERSION` · `API/FLAG` · `PATH/CONFIG` · `PRODUCT-FEATURE` · `FACT` · `OTHER`
Root causes: `STALE-TRAINING` (world moved past training data) · `UNVERIFIED-ASSUMPTION` (guessed instead of checking context) · `SKIPPED-SEARCH` (should have searched, didn't) · `OVERCONFIDENT-SYNTHESIS` (combined true facts into a false one) · `CONTEXT-MISREAD` (info was in-thread, misread)

### 4.5 Prevention mapping (verbatim table — the payload of the skill)
| Root cause | Prevention rule to draft |
|---|---|
| STALE-TRAINING | Search before asserting versions, flags, APIs, product features, prices, or current status |
| UNVERIFIED-ASSUMPTION | State the assumption + confidence inline, or verify before acting |
| SKIPPED-SEARCH | Concrete search-first trigger list: anything post-cutoff, anything the user could disprove with one lookup |
| OVERCONFIDENT-SYNTHESIS | Flag inferred (vs sourced) claims explicitly as inference |
| CONTEXT-MISREAD | Re-read the exact user turn before contradicting or restating it |

### 4.6 Workflow to encode (imperative, numbered, gated)
1. **Window.** Default 30d via `recent_chats` recipe (desc, n=20, `before` pagination, ≤5 calls). Record coverage.
2. **Sweep.** One `conversation_search` per lexicon term, `max_results=10`. Dedupe by chat url. Keep only hits where the correction sits in a human turn (label visible in snippet); else verify with one `read_conversation` open or discard.
3. **Log.** Fill the incident schema. GATE: every row has both a claim and a correction cell — a correction without a recoverable original claim goes to an `UNPAIRED` list, not the log.
4. **Root-cause.** Assign exactly one enum value per incident, with a one-clause justification.
5. **Prevent.** From incidents present, emit only the matching prevention rules, condensed to ≤5 dense lines total, formatted memory-paste-ready.
6. **Optional staging.** Only on `stage rules`: `memory_user_edits view` → E0 → plan with expected E1 → explicit confirm → execute → re-view, GATE observed == E1.
7. **Report.** Incident log + root-cause distribution count + prevention lines + UNPAIRED list + coverage line.

### 4.7 Deep mode (verbatim)
If `/mnt/user-data/uploads/conversations.json` exists (claude.ai export): Python pass — `json.load`; per conversation iterate `chat_messages`; regex lexicon over `sender == "human"` turns; pair each hit with the immediately preceding assistant turn as the claim candidate; output pairs for manual confirmation. Fallback to search sweep on parse failure.

### 4.8 Guardrails (verbatim)
- Never fabricate the "asserted claim" cell; if unrecoverable, the row is UNPAIRED.
- User corrections are treated as ground truth for logging, but note when a correction itself looks uncertain.
- Sensitive personal content: exclude; count as `SKIPPED-SENSITIVE`.
- Zero incidents → report cleanly, no padding.

### 4.9 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Lexicon → Schema + enums → Workflow → Prevention mapping → Deep mode → Output template → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/claim-audit/SKILL.md` | §4.1 + body per §4.2–4.9 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/claim-audit
# write SKILL.md per §4
wc -l < /home/claude/claim-audit/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/claim-audit/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*claim-audit\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['STALE-TRAINING', 'UNPAIRED', 'SKIPPED-SEARCH']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run claim audit" /home/claude/claim-audit/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/claim-audit.zip claim-audit
unzip -l /mnt/user-data/outputs/claim-audit.zip               # EXPECT: claim-audit/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate one incident with a recoverable claim (→ log) and one bare correction (→ UNPAIRED). Confirm prevention lines emit only for root causes present. Fix if not.

## 7. Deliver
Present `/mnt/user-data/outputs/claim-audit.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run claim audit`; (c) D# deviations if any. Nothing else.
