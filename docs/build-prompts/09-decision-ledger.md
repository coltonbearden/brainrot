# BUILD PROMPT 09 — `decision-ledger` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `decision-ledger`: harvest decision language from chat history, normalize entries into one ledger with dates, status, and source links, conflict-check within domains, and write `DECISIONS-GLOBAL.md` as a downloadable file. Deliver `/mnt/user-data/outputs/decision-ledger.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `decision-ledger` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤300), UTF-8, LF, no placeholders |
| Package | zip with `decision-ledger/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `conversation_search` is literal keyword match | One search per marker; markers below |
| `recent_chats` caps at 20/call | Window default 90d for this skill (decisions age slower); `SAMPLED` label if uncovered |
| Assistant recommendations are not decisions | Provenance gate is the core of the skill |
| Summaries (`kind='summary'`) can collapse "suggested" into "decided" | Prefer `kind='conversation'` snippets; a summary-only decision is marked `PROVENANCE-WEAK` |
| Skill output must be user-visible | Ledger written to `/mnt/user-data/outputs/` and presented via the file-presentation tool |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: decision-ledger
description: Harvests decisions from chat history into one normalized ledger with dates, status, and source links. Use for run decision ledger, consolidate decisions, harvest decisions. Flags conflicts.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run decision ledger` · `consolidate decisions` · `harvest decisions` · `decision ledger`

### 4.3 Embedded marker lexicon (verbatim table; tunable)
| Term (one search each) |
|---|
| locked |
| canonical |
| rejected |
| superseded |
| decided |
| final answer |
| going with |
| we'll use |
| DECISIONS.md |
| verdict |
| D1 |
| D-0 |

### 4.4 Entry schema (verbatim)
`DL-### | date (chat updated_at) | decision (own words, one line) | status (ACTIVE / SUPERSEDED / REJECTED) | domain (short tag) | source (chat title + url) | provenance (STRONG / PROVENANCE-WEAK)`

### 4.5 Provenance gate (verbatim, prominent)
An entry qualifies only if a human turn commits ("locked", "canonical", "going with", explicit approval of a named option) or explicitly rejects. Assistant recommendations alone = `PROPOSED` and are excluded from the ledger. When only a model-written summary asserts the decision, log it but mark `PROVENANCE-WEAK` for user confirmation.

### 4.6 Workflow to encode (imperative, numbered, gated)
1. **Window.** Default 90d via `recent_chats` recipe (desc, n=20, `before` pagination, ≤5 calls). Record coverage `FULL|SAMPLED`.
2. **Sweep.** One `conversation_search` per marker, `max_results=10`. Dedupe by chat url + decision topic.
3. **Qualify.** Apply the provenance gate per hit; unclear → one `read_conversation` open (hit `page_token`, ≤2 per candidate) or mark `PROVENANCE-WEAK`.
4. **Normalize.** Fill the §4.4 schema. Same-topic entries: latest human commitment wins `ACTIVE`; earlier ones become `SUPERSEDED` linking the successor id. GATE: no two ACTIVE entries share domain + topic without landing in the conflicts table.
5. **Conflict pass.** Group by domain; list incompatible ACTIVE pairs: `domain | DL-a | DL-b | nature of conflict | needs user ruling`.
6. **Write.** Create `/mnt/user-data/outputs/DECISIONS-GLOBAL.md`: header (date, window, coverage), ledger table sorted by domain then date, conflicts table, `PROVENANCE-WEAK` list, excluded-PROPOSED count. Present the file.
7. **Report.** In-chat: entry count, ACTIVE/SUPERSEDED/REJECTED split, conflict count, link to the file.

### 4.7 Guardrails (verbatim)
- Never merge or resolve a conflict autonomously — conflicts are surfaced for user ruling only.
- Decision text is paraphrase, one line, own words; no long verbatim quoting.
- Hypotheticals and brainstorm options never enter the ledger.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- Re-runs: if the user uploads a prior `DECISIONS-GLOBAL.md` to `/mnt/user-data/uploads/`, merge into it — preserve existing DL-### ids, append new ids after the max.

### 4.8 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Lexicon → Schema → Provenance gate → Workflow → File format spec → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/decision-ledger/SKILL.md` | §4.1 + body per §4.2–4.8 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/decision-ledger
# write SKILL.md per §4
wc -l < /home/claude/decision-ledger/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/decision-ledger/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*decision-ledger\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['PROVENANCE-WEAK', 'SUPERSEDED', 'DECISIONS-GLOBAL.md', 'DL-']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run decision ledger" /home/claude/decision-ledger/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/decision-ledger.zip decision-ledger
unzip -l /mnt/user-data/outputs/decision-ledger.zip                   # EXPECT: decision-ledger/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate three candidates — human-committed (→ ACTIVE, STRONG), assistant-only recommendation (→ excluded PROPOSED), summary-only (→ PROVENANCE-WEAK) — plus a same-topic pair (→ SUPERSEDED chain). Fix if routing fails.

## 7. Deliver
Present `/mnt/user-data/outputs/decision-ledger.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run decision ledger` (attach a prior DECISIONS-GLOBAL.md to merge); (c) D# deviations if any. Nothing else.
