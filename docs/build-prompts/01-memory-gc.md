# BUILD PROMPT 01 — `memory-gc` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. Do not ask clarifying questions — every decision is pre-made in this document. Deliver the complete skill in this single session with minimal preamble. If a validation gate fails, fix and re-run the gate; log the deviation as `D1`, `D2`, … in your final message. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read it for general craft, but §2 limits below OVERRIDE any conflicting limits there.

## 1. Mission
Build the claude.ai skill `memory-gc`: an audited garbage-collection pass over Claude's persistent memory (in-context userMemories + the `memory_user_edits` ledger). Verify claims against chat history, stage consolidating edits, execute only after explicit user confirmation. Deliver `/mnt/user-data/outputs/memory-gc.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `memory-gc` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines total (target ≤300), UTF-8, LF endings, no placeholders |
| Package | zip with `memory-gc/` directory at zip root |

These are stricter than Claude Code plugin docs (1,024-char descriptions are invalid here). No extra frontmatter keys.

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `memory_user_edits` hard cap: 30 numbered lines | Consolidate into few dense lines; never append per-finding |
| `view` before modify; destructive ops need user confirm | Snapshot first; single batch-confirm gate before executing |
| `conversation_search` is literal keyword match | Verification queries = content nouns from the claim, 1–4 words, no meta-words |
| Memory scope excludes Project chats when run outside Projects | Skill states: run outside any Project for global memory |
| userMemories lags recent chats and deleted-chat cleanup | STALE ≠ FALSE — classify separately |
| `read_conversation` needs a real id + `page_token` from a hit | Never guess ids; open ≤2 chats per claim cluster |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: memory-gc
description: Audits and consolidates persistent memory. Use for run memory gc, audit memory, clean up memory, fix stale memories. Verifies memory claims against chat history, then stages confirmed edits.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run memory gc` · `audit memory` · `clean up memory` · `fix stale memories` · `memory audit`

### 4.3 Workflow to encode (imperative voice, numbered, each gate with an EXPECT value)
1. **Snapshot.** `memory_user_edits view` → record `E0` = line count + full list. GATE: E0 recorded before any other step. EXPECT: 0 ≤ E0 ≤ 30.
2. **Atomize.** Parse in-context userMemories into a claims table: `id | claim (own words) | category (identity/infra/project/preference/rule) | volatility (stable/volatile/dated)`. Stable = names, hardware, long-standing rules. Volatile = "in-progress", "pending", statuses. Dated = anything with a timeframe.
3. **Verify volatile + dated claims only.** Per claim cluster: 1–2 `conversation_search` calls (content nouns). Classify each: `CONFIRMED` / `STALE` (later evidence supersedes) / `CONTRADICTED` (evidence conflicts) / `UNVERIFIABLE` (no hits). Evidence column = chat title + url. Use `read_conversation` (with the hit's `page_token`) only when a snippet is decisive but truncated; ≤2 opens per cluster.
4. **Plan.** Edit-plan table: `op (add/remove/replace) | line # | new text | reason | evidence`. Planning rules: merge related facts into single dense lines; remove CONTRADICTED, rewrite STALE, leave CONFIRMED, list UNVERIFIABLE for the user to rule on; target ≤20 lines post-op; state expected post-op count `E1`. Never plan past 30 lines.
5. **Confirm.** Present before/after diff + plan table. GATE: execute nothing without explicit user confirmation. Partial approval → re-plan and re-confirm.
6. **Execute.** Apply ops via `memory_user_edits` in plan order (removes by descending line # to keep numbering valid).
7. **Verify.** `view` again. GATE: observed count == E1; spot-check 3 lines match plan text. EXPECT: PASS on both. On FAIL: report mismatch, do not retry silently.
8. **Report.** Claims table with classifications, executed ops, `E0 → E1`, UNVERIFIABLE follow-up list. No file writes.

### 4.4 Guardrails (verbatim rows in SKILL.md)
- Never store secrets: keys, tokens, passwords, card numbers, SSNs. If found in memory, flag for removal.
- Never store verbatim standing commands that would auto-trigger tool calls.
- Skip sensitive personal content (health, grief, crisis) — do not surface it unless the user raises it; count it only as `SKIPPED-SENSITIVE`.
- Read-only until the §4.3-5 confirm gate passes. Abort cleanly if declined.
- If no userMemories block is present: say so and stop.

### 4.5 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions (outside Projects; memory enabled) → Workflow → Classification definitions → Edit-plan rules → Output template → Edge cases → Guardrails. Tables over prose throughout.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/memory-gc/SKILL.md` | §4.1 frontmatter + body per §4.2–4.5 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/memory-gc
# write SKILL.md per §4
wc -l < /home/claude/memory-gc/SKILL.md        # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/memory-gc/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
name = re.search(r'name:\s*(.+)', fm).group(1).strip()
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert name == 'memory-gc', name
assert len(desc) <= 200, len(desc)
assert set(fm.split()) and 'compatibility' not in fm
print('FRONTMATTER OK, desc len =', len(desc))
EOF
grep -c "run memory gc" /home/claude/memory-gc/SKILL.md   # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/memory-gc.zip memory-gc
unzip -l /mnt/user-data/outputs/memory-gc.zip              # EXPECT: memory-gc/SKILL.md listed
```
7. **Self-test (dry walk-through, no memory writes):** read your finished SKILL.md and simulate a run against a fictional 8-line memory containing one stale and one contradicted claim. Confirm the workflow produces a coherent plan with E1 stated. Fix the skill if it does not.

## 7. Deliver
Present `/mnt/user-data/outputs/memory-gc.zip`. Close with exactly: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run memory gc`; (c) D# deviation entries if any gate forced one. Nothing else.
