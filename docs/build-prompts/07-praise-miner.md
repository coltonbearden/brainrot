# BUILD PROMPT 07 — `praise-miner` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `praise-miner`: mine chat history for praised, zero-correction outputs, extract the structural antecedents (format, prompt shape, delegation pattern) that preceded first-try success, and codify do-more rules with optional gated staging. Deliver `/mnt/user-data/outputs/praise-miner.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `praise-miner` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤300), UTF-8, LF, no placeholders |
| Package | zip with `praise-miner/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `conversation_search` is literal keyword match | One search per positive term; `within_conversation_id` for the clean-check probe |
| `recent_chats` caps at 20/call | Window default 30d; `SAMPLED` label if uncovered |
| Praise ≠ decision; assistant suggestions ≠ user choices | Provenance rule below governs every extracted rule |
| Snippets truncate | Antecedent extraction requires opening the thread, not inferring from snippet |
| `memory_user_edits` cap 30 | Do-more rules condensed ≤5 dense lines; staging behind confirm gate |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: praise-miner
description: Mines chat history for praised, zero-correction outputs and extracts the formats and prompt shapes behind them. Use for run praise miner, what works well, success patterns. Outputs do-more rules.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run praise miner` · `what works well` · `success patterns` · `praise miner`

### 4.3 Embedded lexicon (verbatim table; tunable)
| Positive terms | Strength |
|---|---|
| perfect | strong |
| exactly what | strong |
| ship it | strong |
| nailed | strong |
| first try | strong |
| works great | strong |
| love it | medium |
| that works | medium |
| beautiful | medium |
| exactly | weak — pairing rule |
| great | weak — pairing rule |

**Pairing rule:** weak terms count only when the snippet shows the praise directed at an assistant output (not at a third party or the user's own work).

### 4.4 Clean-check heuristic (verbatim)
A praised chat is `CLEAN` only if two negative probes inside it return zero hits: `conversation_search(query="no I said", within_conversation_id=<uuid>)` and `conversation_search(query="wrong", within_conversation_id=<uuid>)`. Any hit → `MIXED` (still logged, weighted half).

### 4.5 Antecedent dimensions (verbatim)
`FORMAT` (table / code block / file artifact / inline prose) · `PROMPT-SHAPE` (spec-first? constraints enumerated? examples given? gates requested?) · `DELEGATION` (answered in chat vs produced a build prompt vs produced files) · `LENGTH` (terse vs long) · `GATES-PRESENT` (verification steps included?)

### 4.6 Workflow to encode (imperative, numbered, gated)
1. **Window.** Default 30d via `recent_chats` recipe (desc, n=20, `before` pagination, ≤5 calls). Record coverage.
2. **Sweep.** One `conversation_search` per positive term, `max_results=10`. Dedupe by chat url. Apply pairing rule.
3. **Clean-check.** Run §4.4 on each praised chat. Table: `chat | praise term | CLEAN|MIXED`.
4. **Extract.** For up to 5 CLEAN chats (most recent first): open via `read_conversation` at the praise hit's `page_token`, page back to the originating request, and record all five §4.5 dimensions. GATE: no antecedent row without an actual open — snippet-only inference is forbidden.
5. **Codify.** Aggregate: a do-more rule requires the same antecedent value in ≥2 CLEAN chats. Rules table: `antecedent | evidence count | rule draft (dense, memory-ready)`. Below threshold → observations list.
6. **Provenance gate.** Rules describe what to do more of; they never assert the user "decided" anything. Assistant self-suggestions praised in passing are excluded.
7. **Optional staging.** Only on `stage rules`: `memory_user_edits view` → E0 → plan with expected E1 → explicit confirm → execute → re-view, GATE observed == E1.
8. **Report.** Clean-check table + rules table + observations + coverage line.

### 4.7 Guardrails (verbatim)
- Never promote praise into a decision or standing preference without the ≥2-chat threshold.
- Politeness ("thanks") is not praise; require an evaluative term.
- Sensitive personal content excluded; count as `SKIPPED-SENSITIVE`.
- Zero CLEAN chats → report the MIXED table and stop; no fabricated rules.

### 4.8 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Lexicon → Clean-check → Antecedent dimensions → Workflow → Output template → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/praise-miner/SKILL.md` | §4.1 + body per §4.2–4.8 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/praise-miner
# write SKILL.md per §4
wc -l < /home/claude/praise-miner/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/praise-miner/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*praise-miner\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['within_conversation_id', 'CLEAN', 'MIXED', '≥2']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run praise miner" /home/claude/praise-miner/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/praise-miner.zip praise-miner
unzip -l /mnt/user-data/outputs/praise-miner.zip                # EXPECT: praise-miner/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate two CLEAN chats sharing `FORMAT = table` (→ rule) and one antecedent appearing once (→ observation only). Fix if the thresholds don't bite.

## 7. Deliver
Present `/mnt/user-data/outputs/praise-miner.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run praise miner`; (c) D# deviations if any. Nothing else.
