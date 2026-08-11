# BUILD PROMPT 04 — `handoff-distill` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions are pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `handoff-distill`: distill the current session (or a named past chat) into a canonical handoff block — decisions, evidence-backed completions, open items, exact absolute paths, verification state, and a paste-ready next-session prompt. Deliver `/mnt/user-data/outputs/handoff-distill.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `handoff-distill` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤280), UTF-8, LF, no placeholders |
| Package | zip with `handoff-distill/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| Primary input is the live conversation | Default scope = current chat; no search needed |
| Past chats reachable only via `conversation_search` → `read_conversation` with a hit `page_token` | Named-chat mode: search topic nouns, open at hit, page adjacent turns only |
| Assistant proposals are not user decisions | Provenance rule is the core of the skill (below) |
| Assistant memory of "done" is unreliable | Completion requires visible evidence in-thread |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: handoff-distill
description: Distills a session into a canonical handoff: decisions, open items, exact paths, verification state, next-session prompt. Use for handoff, distill this session, prep next session.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`handoff` · `distill this session` · `prep next session` · `session handoff` · `handoff block`

### 4.3 Provenance rule (verbatim, prominent in SKILL.md)
Only these count as ground truth: explicit user statements, executed tool output visible in the thread, and files/artifacts actually produced. Assistant recommendations, drafts, and plans are `PROPOSED` — never promoted to `DECIDED` or `DONE` without a user commitment in a human turn. Hypotheticals stay hypothetical.

### 4.4 Handoff template (embed verbatim as the output contract)
```
## HANDOFF — <title> — <YYYY-MM-DD>
### Decisions (locked)
| id | decision | source (turn/quote paraphrase) |
### Completed (evidence-backed)
| item | evidence (command run / output / file path / url) |
### Proposed (not yet decided)
| item | proposer | status |
### Open items
| id | item | blocker | exact next action |
### Exact paths & environments
| what | absolute path or host | shell/env |
### Verification state
| check | expected | observed | status |
### Next-session prompt
<one paste-ready prompt: goal, constraints, questions front-loaded, all outputs written to files, absolute paths only>
```

### 4.5 Workflow to encode (imperative, numbered, gated)
1. **Scope.** Default = current conversation. If the user names another chat: `conversation_search` with content nouns from their reference; open the best hit via `read_conversation` (hit `page_token`); page adjacent turns only; ≤2 chats total. If the reference is too vague to search, ask which chat — the single permitted question.
2. **Extract.** Fill the §4.4 template applying the provenance rule to every row.
3. **Gates before output.** (a) Every path in "Exact paths" is absolute — zero shorthand like "the repo". (b) Every Completed row has a non-empty evidence cell. (c) Next-session prompt contains zero unresolved placeholders or bracketed TODOs. (d) Anything failing a gate moves to Proposed or Open — never silently dropped. EXPECT: all four gates PASS, stated in one line above the block.
4. **Output.** The handoff block in-chat. File write only on request: `/mnt/user-data/outputs/HANDOFF-<slug>-<YYYYMMDD>.md`, then present it.

### 4.6 Edge cases (verbatim)
- Empty/near-empty session → minimal block with Open items only; say so.
- Conflicting decisions in-thread → latest user statement wins; earlier entry marked `SUPERSEDED` with both sources.
- Session spans multiple projects/topics → one block per topic, max 3, else ask the user to pick.

### 4.7 Guardrails (verbatim)
- Never fabricate evidence cells; `evidence: none found` is a valid cell that forces the row into Open/Proposed.
- Paraphrase user turns; no long verbatim quoting.
- Sensitive personal content appears in the handoff only if the user raised it as a work item.

### 4.8 SKILL.md body structure (fixed order)
Purpose → Triggers → Provenance rule → Workflow → Template → Gates → Edge cases → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/handoff-distill/SKILL.md` | §4.1 + body per §4.2–4.8 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/handoff-distill
# write SKILL.md per §4
wc -l < /home/claude/handoff-distill/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/handoff-distill/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*handoff-distill\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['PROPOSED', 'Verification state', 'Next-session prompt', 'absolute']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "distill this session" /home/claude/handoff-distill/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/handoff-distill.zip handoff-distill
unzip -l /mnt/user-data/outputs/handoff-distill.zip                    # EXPECT: handoff-distill/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate distilling a fictional session where the assistant proposed X, the user approved Y, and one command ran with visible output. Confirm X lands in Proposed, Y in Decisions, the command in Completed with evidence. Fix the skill if not.

## 7. Deliver
Present `/mnt/user-data/outputs/handoff-distill.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — at the end of any working session, say `handoff`; (c) D# deviations if any. Nothing else.
