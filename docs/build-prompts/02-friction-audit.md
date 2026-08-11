# BUILD PROMPT 02 — `friction-audit` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. Do not ask clarifying questions — every decision is pre-made in this document. Deliver the complete skill in this single session with minimal preamble. If a validation gate fails, fix and re-run; log deviations as `D1`, `D2`, …. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read it for craft; §2 limits below OVERRIDE any conflicts.

## 1. Mission
Build the claude.ai skill `friction-audit`: a windowed sweep of chat history for user frustration and correction patterns, clustered into a behavior taxonomy, ranked, with one remediation per pattern and optional gated memory staging. Deliver `/mnt/user-data/outputs/friction-audit.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `friction-audit` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines total (target ≤320), UTF-8, LF, no placeholders |
| Package | zip with `friction-audit/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `conversation_search` is literal keyword match | Sweep = one search per lexicon term; content-noun phrasing; no dates/meta-words |
| `recent_chats` caps at 20/call; ~5 calls practical | Window bounding recipe below; mark results `SAMPLED` if window uncovered |
| Project chats invisible from outside Projects | Skill states: run outside Projects for global sweep; inside a Project for that Project |
| `read_conversation` needs real id + hit `page_token` | Evidence etiquette: ≤2 opens per top pattern, cite title + url, paraphrase only |
| Search hits are snippets, may truncate mid-turn | Attribute speaker only when the `Human:`/`Assistant:` label is visible |
| `memory_user_edits` cap 30; destructive ops need confirm | Staging is optional and always behind a confirm gate |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: friction-audit
description: Mines chat history for user frustration and correction patterns. Use for run friction audit, what annoys me, find my complaints. Ranks patterns and stages one fix per pattern.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run friction audit` · `what annoys me` · `find my complaints` · `frustration audit` · `friction patterns`

### 4.3 Embedded lexicon (verbatim table in SKILL.md; marked tunable)
| Term (one search each) | Strength |
|---|---|
| no I said | strong |
| that's not what | strong |
| you ignored | strong |
| I already told | strong |
| not what I asked | strong |
| still wrong | strong |
| re-read | medium |
| stop doing | medium |
| why did you | medium |
| didn't ask | medium |
| as I said | medium |
| you keep | medium |
| wrong path | medium |
| undo that | medium |
| again | weak — pairing rule required |
| wrong | weak — pairing rule required |

**Pairing rule:** weak terms count only if the snippet also shows a second lexicon marker or an imperative correction; otherwise discard the hit.

### 4.4 Taxonomy (verbatim)
`FORMAT` (unwanted bullets/length/structure) · `PATH-VAGUE` (missing absolute paths/targets) · `ASSUMPTION` (acted without ground truth) · `IGNORED-INSTRUCTION` · `VERBOSITY-PREAMBLE` · `HALLUCINATION` (note: deep-dive belongs to claim-audit if installed) · `TOOL-MISUSE` · `SCOPE-CREEP` · `OTHER`

### 4.5 Workflow to encode (imperative, numbered, gated)
1. **Window.** Default 30d; accept `7d` if the user says so. Bound via `recent_chats` (desc, n=20, paginate `before` = earliest `updated_at`, ≤5 calls). Record: chats seen `C`, coverage `FULL|SAMPLED`. GATE: window bounds stated before sweeping.
2. **Sweep.** One `conversation_search` per lexicon term, `max_results=10`. Dedupe hits by chat url. Apply pairing rule to weak terms. Discard hits whose `updated_at` predates the window.
3. **Cluster.** Assign each hit a taxonomy label from the snippet. Ambiguous → `OTHER`, never force-fit.
4. **Rank.** Score = hit count × recency weight (≤7d ×3, ≤30d ×1). Output ranked table: `pattern | hits | recency | example (short paraphrase) | chats (title+url)`.
5. **Evidence.** For the top 3 patterns only: ≤2 `read_conversation` opens each (hit `page_token`) to confirm the paraphrase is fair.
6. **Remediate.** One remediation per pattern, typed: `MEMORY-EDIT` (draft the exact dense line) / `SKILL-CANDIDATE` (name + one-line purpose) / `PROMPT-PATTERN` (what to include in future prompts). GATE: exactly one primary remediation per pattern.
7. **Optional staging.** Only if the user says `stage fixes`: `memory_user_edits view` → record E0 → present plan with expected E1 → explicit confirm → execute → re-view, GATE observed == E1.
8. **Report.** Ranked table + remediation table + coverage line (`C chats, FULL|SAMPLED`). No silent extrapolation beyond sampled counts.

### 4.6 Deep mode (verbatim section in SKILL.md)
If `/mnt/user-data/uploads/` contains a claude.ai export (`conversations.json`): prefer a full-history Python pass. Recipe to embed: `json.load`; iterate conversations → `name`, `uuid`, `chat_messages[]`; keep turns where `sender == "human"`; regex the lexicon over turn text; aggregate counts per term per conversation; report top conversations by hit density. Fall back to search sweep if parsing fails.

### 4.7 Guardrails (verbatim)
- Sensitive personal content (health, grief, crisis): exclude from the report; count only as `SKIPPED-SENSITIVE`.
- Paraphrase evidence; never reproduce long verbatim passages.
- Read-only unless the §4.5-7 confirm gate passes.
- Zero hits → report "no friction markers found in window" and stop; do not pad findings.

### 4.8 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Lexicon → Taxonomy → Workflow → Deep mode → Output template → Edge cases → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/friction-audit/SKILL.md` | §4.1 + body per §4.2–4.8 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/friction-audit
# write SKILL.md per §4
wc -l < /home/claude/friction-audit/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/friction-audit/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*friction-audit\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for term in ['no I said', 'you ignored', 'SKIPPED-SENSITIVE']:
    assert term in t, term
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run friction audit" /home/claude/friction-audit/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/friction-audit.zip friction-audit
unzip -l /mnt/user-data/outputs/friction-audit.zip                  # EXPECT: friction-audit/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate a run over three fictional hits (one weak-term hit that the pairing rule must discard). Confirm the ranked table, one-remediation rule, and coverage line all materialize. Fix the skill if not.

## 7. Deliver
Present `/mnt/user-data/outputs/friction-audit.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run friction audit` (add `7d` for a tight window); (c) D# deviations if any. Nothing else.
