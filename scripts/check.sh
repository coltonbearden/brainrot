#!/usr/bin/env bash
# brainrot check suite — every repo invariant in one runnable place.
#
#   bash scripts/check.sh [--scrub <token-file>]
#
# Each section prints PASS, FAIL, or SKIP: <reason>; a summary line closes the
# run, and the exit code is nonzero if any section FAILed. A missing optional
# tool is a SKIP, never a FAIL. No network calls; writes nothing outside dist/
# (and removes the dist/ it creates).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"

SCRUB_FILE="${BRAINROT_SCRUB_TOKENS:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scrub) SCRUB_FILE="${2:?--scrub needs a path}"; shift 2 ;;
    *) echo "unknown argument: $1 (usage: check.sh [--scrub <token-file>])" >&2; exit 2 ;;
  esac
done

PASSED=0 FAILED=0 SKIPPED=0

report() { # report <num> <name> <PASS|FAIL|SKIP> [reason]
  local num="$1" name="$2" verdict="$3" reason="${4:-}"
  case "$verdict" in
    PASS) PASSED=$((PASSED + 1)) ;;
    FAIL) FAILED=$((FAILED + 1)) ;;
    SKIP) SKIPPED=$((SKIPPED + 1)) ;;
  esac
  if [[ -n "$reason" ]]; then
    printf '[%s/8] %-22s %s: %s\n' "$num" "$name" "$verdict" "$reason"
  else
    printf '[%s/8] %-22s %s\n' "$num" "$name" "$verdict"
  fi
}

detail() { # indented context under the current section
  printf '      %s\n' "$1"
}

# ── 1. official plugin/marketplace manifest validation ──────────────────────
if command -v claude >/dev/null 2>&1; then
  ok=1
  claude plugin validate . >/dev/null 2>&1 || { ok=0; detail "claude plugin validate . failed"; }
  claude plugin validate ./plugins/brainrot >/dev/null 2>&1 || { ok=0; detail "claude plugin validate ./plugins/brainrot failed"; }
  if [[ $ok -eq 1 ]]; then report 1 "plugin manifests" PASS; else report 1 "plugin manifests" FAIL; fi
else
  report 1 "plugin manifests" SKIP "claude not on PATH (expected on CI runners)"
fi

# ── 2. structural + frontmatter invariants ──────────────────────────────────
if command -v python3 >/dev/null 2>&1; then
  if out="$(python3 plugins/brainrot/scripts/validate.py 2>&1)" && [[ "$out" == OK* ]]; then
    report 2 "validate.py" PASS
  else
    report 2 "validate.py" FAIL
    detail "$out"
  fi
else
  report 2 "validate.py" SKIP "python3 not on PATH"
fi

# ── 3. shellcheck over all shell scripts (including this one) ───────────────
if command -v shellcheck >/dev/null 2>&1; then
  if out="$(shellcheck scripts/*.sh plugins/brainrot/scripts/*.sh 2>&1)"; then
    report 3 "shellcheck" PASS
  else
    report 3 "shellcheck" FAIL
    detail "$out"
  fi
else
  report 3 "shellcheck" SKIP "shellcheck not installed"
fi

# ── 4. banner smoke: all three modes emit non-empty output ──────────────────
ok=1
o1="$(bash scripts/banner.sh 2>/dev/null)" || ok=0
o2="$(bash scripts/banner.sh --small 2>/dev/null)" || ok=0
o3="$(NO_COLOR=1 bash scripts/banner.sh --plain 2>/dev/null)" || ok=0
if [[ $ok -eq 1 && -n "$o1" && -n "$o2" && -n "$o3" ]]; then
  report 4 "banner smoke" PASS
else
  report 4 "banner smoke" FAIL
  [[ -z "$o1" ]] && detail "default banner produced no output"
  [[ -z "$o2" ]] && detail "--small banner produced no output"
  [[ -z "$o3" ]] && detail "NO_COLOR=1 --plain banner produced no output"
fi

# ── 5. claude.ai zip packaging round-trip (set equality vs skills/) ─────────
if [[ -d dist && -n "$(ls -A dist 2>/dev/null)" ]]; then
  report 5 "zip packaging" SKIP "dist/ already exists and is non-empty — not clobbering it"
elif ! command -v zip >/dev/null 2>&1; then
  report 5 "zip packaging" SKIP "zip not installed"
else
  bash plugins/brainrot/scripts/package_claude_ai_zips.sh >/dev/null
  zips="$(cd dist && shopt -s nullglob && for z in *.zip; do printf '%s\n' "${z%.zip}"; done | sort)"
  # The command-style skills (arbitrate, runbook) are deliberately not packaged
  # for claude.ai — their surface there is the paste-in prompt. Keep this filter
  # in sync with COMMAND_SKILLS in package_claude_ai_zips.sh.
  skills="$(cd plugins/brainrot/skills && for d in */; do printf '%s\n' "${d%/}"; done | grep -vx -e arbitrate -e runbook | sort)"
  if [[ "$zips" == "$skills" ]]; then
    report 5 "zip packaging" PASS
  else
    report 5 "zip packaging" FAIL
    detail "zip set does not equal the set of skill directories:"
    detail "only in dist/:   $(comm -23 <(printf '%s\n' "$zips") <(printf '%s\n' "$skills") | tr '\n' ' ')"
    detail "only in skills/: $(comm -13 <(printf '%s\n' "$zips") <(printf '%s\n' "$skills") | tr '\n' ' ')"
  fi
  rm -rf dist
fi

# ── 6. site static checks on docs/index.html ────────────────────────────────
site=docs/index.html
ok=1
if [[ ! -f "$site" ]]; then
  report 6 "site static checks" FAIL
  detail "$site does not exist"
else
  if grep -qi '<script' "$site"; then
    ok=0; detail "found a <script occurrence (site must have zero script tags)"
  fi
  while IFS= read -r a; do
    if ! grep -q "id=\"$a\"" "$site"; then
      ok=0; detail "href=\"#$a\" has no matching id"
    fi
  done < <(grep -o 'href="#[^"]*"' "$site" | sed 's/^href="#//; s/"$//' | sort -u)
  size="$(wc -c < "$site")"
  if [[ "$size" -ge 122880 ]]; then
    ok=0; detail "file is ${size} bytes (limit 122880 = 120KB)"
  fi
  if grep -qiE 'unpkg|react|support\.js|__bundler' "$site"; then
    ok=0; detail "found a banned token (unpkg/react/support.js/__bundler)"
  fi
  # The og:image link-preview card — the sole .png exception (issue #14). The
  # filename is derived from the meta tag, not hardcoded, so a rename that
  # leaves the file behind cannot pass.
  if ! grep -q '<meta name="twitter:card" content="summary_large_image">' "$site"; then
    ok=0; detail "twitter:card must be summary_large_image (the card is 1.91:1)"
  fi
  card_url="$(grep -o '<meta property="og:image" content="[^"]*"' "$site" \
              | sed 's/.*content="//; s/"$//')"
  if [[ -z "$card_url" ]]; then
    ok=0; detail "no og:image meta tag"
  else
    if [[ "$card_url" != https://coltonbearden.github.io/brainrot/* ]]; then
      ok=0; detail "og:image must be an absolute site URL, got: $card_url"
    fi
    if ! grep -qF "<meta name=\"twitter:image\" content=\"$card_url\">" "$site"; then
      ok=0; detail "twitter:image does not match og:image ($card_url)"
    fi
    card="docs/${card_url##*/}"
    if [[ ! -f "$card" ]]; then
      ok=0; detail "og:image points at $card_url but $card does not exist"
    elif command -v python3 >/dev/null 2>&1; then
      if dims="$(python3 - "$card" <<'PY'
import struct, sys
head = open(sys.argv[1], "rb").read(24)
if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
    sys.exit("not a PNG")
print("%dx%d" % struct.unpack(">II", head[16:24]))
PY
      )"; then
        [[ "$dims" == "1200x630" ]] || { ok=0; detail "$card is $dims, must be 1200x630"; }
      else
        ok=0; detail "$card is not a readable PNG"
      fi
      # ...and it must still be exactly what the generator draws, so the card
      # cannot go stale when the mascot art changes. --check re-renders in
      # memory and compares decoded pixels, never the compressed bytes: zlib's
      # output can differ between builds, the pixels cannot.
      gen=scripts/make_og_card.py
      if [[ ! -f "$gen" ]]; then
        ok=0; detail "$gen is missing — cannot verify $card is current"
      elif ! drift="$(python3 "$gen" --check 2>&1)"; then
        ok=0
        while IFS= read -r line; do [[ -n "$line" ]] && detail "$line"; done <<< "$drift"
      fi
    fi
  fi
  if command -v python3 >/dev/null 2>&1; then
    if ! parse_out="$(python3 - "$site" <<'PY'
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}

class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}> before </{tag}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"stray </{tag}>")

p = Balance()
with open(sys.argv[1], encoding="utf-8") as f:
    p.feed(f.read())
p.close()
p.errors.extend(f"unclosed <{t}>" for t in p.stack)
print("\n".join(p.errors))
sys.exit(1 if p.errors else 0)
PY
    )"; then
      ok=0
      detail "html.parser balance check failed:"
      while IFS= read -r line; do [[ -n "$line" ]] && detail "  $line"; done <<< "$parse_out"
    fi
  else
    detail "note: html.parser balance sub-check skipped (python3 absent)"
  fi
  if [[ $ok -eq 1 ]]; then report 6 "site static checks" PASS; else report 6 "site static checks" FAIL; fi
fi

# ── 7. referenced paths exist ────────────────────────────────────────────────
ok=1
while read -r p; do
  [[ -e "$p" ]] || { ok=0; detail "missing: $p"; }
done <<'EOF'
LICENSE
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
assets/banner.svg
assets/mascot.txt
assets/mascot.svg
assets/mascot-mark.svg
docs/index.html
docs/og-card.png
docs/build-prompts
scripts/make_og_card.py
plugins/brainrot/docs/runbook.md
plugins/brainrot/docs/surfaces.md
plugins/brainrot/docs/arbitrate-prompt.md
plugins/brainrot/fixtures/example-cycle
EOF
if [[ $ok -eq 1 ]]; then report 7 "referenced paths" PASS; else report 7 "referenced paths" FAIL; fi

# ── 8. optional scrub scan over tracked files ────────────────────────────────
if [[ -z "$SCRUB_FILE" ]]; then
  report 8 "scrub scan" SKIP "no token file (--scrub <path> or \$BRAINROT_SCRUB_TOKENS)"
elif [[ ! -r "$SCRUB_FILE" ]]; then
  report 8 "scrub scan" FAIL
  detail "token file not readable: $SCRUB_FILE"
else
  ok=1
  while IFS= read -r tok; do
    [[ -z "$tok" ]] && continue
    hits="$(git ls-files -z | xargs -0 grep -liF -- "$tok" 2>/dev/null || true)"
    if [[ -n "$hits" ]]; then
      ok=0
      detail "token hit: $(tr '\n' ' ' <<< "$hits")"
    fi
  done < "$SCRUB_FILE"
  if [[ $ok -eq 1 ]]; then report 8 "scrub scan" PASS; else report 8 "scrub scan" FAIL; fi
fi

# ── summary ──────────────────────────────────────────────────────────────────
printf 'summary: %d passed, %d failed, %d skipped\n' "$PASSED" "$FAILED" "$SKIPPED"
[[ "$FAILED" -eq 0 ]]
