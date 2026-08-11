# BUILD PROMPT 10 — `usage-retro` (claude.ai web skill)

**Session contract:** Fresh context. claude.ai web, code execution + file creation ON. No clarifying questions — decisions pre-made here. Deliver in this session, minimal preamble. Gate failures: fix, re-run, log as `D#`. If `/mnt/skills/examples/skill-creator/SKILL.md` exists, read for craft; §2 limits OVERRIDE conflicts.

## 1. Mission
Build the claude.ai skill `usage-retro`: a sampled 7-or-30-day usage retrospective — thread counts, correction rate, delegation ratio, positive rate, top topics — with trend diffing against a prior retro file and a top-3 actions table, written to a dated file. Deliver `/mnt/user-data/outputs/usage-retro.zip`.

## 2. Hard format constraints (claude.ai skill upload — validated limits)
| Constraint | Required value |
|---|---|
| Frontmatter | YAML, exactly two keys: `name`, `description` |
| `name` | `usage-retro` — lowercase, must equal directory name |
| `description` | ≤200 characters, third person, contains trigger phrases |
| SKILL.md | <500 lines (target ≤300), UTF-8, LF, no placeholders |
| Package | zip with `usage-retro/` at zip root |

## 3. Platform realities the skill body must encode
| Reality | Design consequence |
|---|---|
| `recent_chats` caps at 20/call, ~5 calls practical | Thread count is exact only up to ~100 chats; beyond → `≥100 (capped)` |
| `conversation_search` returns top hits, not exhaustive counts | All rate metrics are sampled; anti-fabrication rules below are mandatory |
| No cross-session state | Trend diffing works only if the user attaches the prior `RETRO-*.md` |
| Project chats invisible from outside Projects | State: run outside Projects; per-Project retro runs inside one |
| Output must be user-visible and reusable next period | Write dated file to `/mnt/user-data/outputs/` and present it |

## 4. Skill specification

### 4.1 Frontmatter (copy verbatim)
```yaml
---
name: usage-retro
description: Builds a sampled 7 or 30 day usage retrospective: thread counts, correction rate, delegation ratio, trends, top actions. Use for run usage retro, weekly retro, monthly retro.
---
```

### 4.2 Trigger phrases (all must appear in the body)
`run usage retro` · `weekly retro` · `monthly retro` · `usage retro`

### 4.3 Metric definitions (verbatim table — each with its probe and honest denominator)
| Metric | How measured | Report form |
|---|---|---|
| threads_in_window | `recent_chats` pagination count | exact, or `≥N (capped)` |
| correction_rate | distinct chats hit by probes `no I said` · `that's not` · `wrong` (pairing rule: `wrong` needs a second marker in-snippet) ÷ threads_in_window | `X/N sampled` |
| delegation_ratio | distinct chats hit by probes `Claude Code` · `build prompt` ÷ threads_in_window | `X/N sampled` |
| positive_rate | distinct chats hit by probes `perfect` · `ship it` · `works great` ÷ threads_in_window | `X/N sampled` |
| top_topics | top 5 recurring content nouns across chat titles from the `recent_chats` pass | list, counts |

### 4.4 Anti-fabrication rules (verbatim, prominent — the identity of this skill)
- Every rate carries its sampled denominator; never a bare percentage.
- Never extrapolate beyond the window or the sample.
- A metric that cannot be measured with available tools is reported `N/A (not measurable via search)` — not estimated.
- Probe hit counts are lower bounds; state `≥` when the search may have truncated.
- Trend deltas are computed only between identically defined metrics; definition changes reset the baseline and say so.

### 4.5 Workflow to encode (imperative, numbered, gated)
1. **Window.** `7d` on `weekly retro`, else 30d. Bound via `recent_chats` (desc, n=20, `before` = earliest `updated_at`, ≤5 calls). Record threads_in_window + coverage `FULL|SAMPLED|CAPPED`. GATE: window and denominator stated before any rate.
2. **Probes.** Run each §4.3 probe as one `conversation_search`, `max_results=10`, dedupe by chat url, discard hits outside the window.
3. **Compute.** Fill the metrics table under the §4.4 rules.
4. **Trend.** If `/mnt/user-data/uploads/` contains a prior `RETRO-*.md`: parse its metrics table, emit a delta column (`↑ ↓ →` + raw change). Absent → `no baseline attached`.
5. **Actions.** Top-3 actions table: `action | metric it moves | first step`. Each action must trace to a measured metric — no generic advice. GATE: 3 rows, each with a metric reference.
6. **Write.** `/mnt/user-data/outputs/RETRO-<YYYYMMDD>.md`: header (date, window, coverage), metrics table (+delta column when baseline present), top_topics, actions table, one-line method note ("sampled via keyword probes; lower bounds"). Present the file.
7. **Report.** In-chat: the metrics table and actions table only; point to the file for the rest.

### 4.6 Guardrails (verbatim)
- Sensitive personal content never appears in top_topics or examples; count as `SKIPPED-SENSITIVE`.
- If threads_in_window = 0: report empty window, write no file, stop.
- The skill's numbers inform, never accuse — no psychological framing of the user's behavior.

### 4.7 SKILL.md body structure (fixed order)
Purpose → Triggers → Preconditions → Metric definitions → Anti-fabrication rules → Workflow → File format spec → Guardrails.

## 5. Files to produce
| Path | Content |
|---|---|
| `/home/claude/usage-retro/SKILL.md` | §4.1 + body per §4.2–4.7 |

## 6. Build steps + validation gates (this session)
```bash
mkdir -p /home/claude/usage-retro
# write SKILL.md per §4
wc -l < /home/claude/usage-retro/SKILL.md   # EXPECT: <500
python3 - <<'EOF'
import re
t = open('/home/claude/usage-retro/SKILL.md').read()
fm = re.search(r'^---\n(.*?)\n---', t, re.S).group(1)
assert re.search(r'name:\s*usage-retro\s*$', fm, re.M)
desc = re.search(r'description:\s*(.+)', fm).group(1).strip()
assert len(desc) <= 200, len(desc)
for s in ['N/A (not measurable via search)', 'sampled', 'RETRO-']:
    assert s in t, s
print('GATES OK, desc len =', len(desc))
EOF
grep -c "run usage retro" /home/claude/usage-retro/SKILL.md  # EXPECT: >=1
cd /home/claude && zip -r /mnt/user-data/outputs/usage-retro.zip usage-retro
unzip -l /mnt/user-data/outputs/usage-retro.zip               # EXPECT: usage-retro/SKILL.md listed
```
7. **Self-test (dry walk-through):** simulate a 30d window of 40 threads, 6 correction hits, no baseline file. Confirm output shows `6/40 sampled`, `no baseline attached`, and 3 metric-traced actions. Fix if any anti-fabrication rule is violable.

## 7. Deliver
Present `/mnt/user-data/outputs/usage-retro.zip`. Close with: (a) install path — Settings → Capabilities → Skills → Upload skill; (b) usage line — new chat outside any Project, say `run usage retro` or `weekly retro` (attach last RETRO-*.md for trends); (c) D# deviations if any. Nothing else.
