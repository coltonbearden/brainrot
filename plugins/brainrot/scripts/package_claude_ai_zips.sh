#!/usr/bin/env bash
# Package each skill as an individually uploadable claude.ai zip (dist/<skill>.zip,
# with <skill>/SKILL.md at the zip root — the layout Settings > Capabilities > Skills expects).
#
# The two command-style skills (arbitrate, runbook) are Claude Code front ends;
# on claude.ai their surface is the paste-in prompt (docs/arbitrate-prompt.md),
# so they are not packaged. See docs/surfaces.md.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILLS="$HERE/../skills"
DIST="$HERE/../../../dist"
COMMAND_SKILLS=(arbitrate runbook)
mkdir -p "$DIST"
for d in "$SKILLS"/*/; do
  name="$(basename "$d")"
  for skip in "${COMMAND_SKILLS[@]}"; do
    [[ "$name" == "$skip" ]] && continue 2
  done
  rm -f "$DIST/$name.zip"
  (cd "$SKILLS" && zip -qr "$DIST/$name.zip" "$name")
  echo "dist/$name.zip"
done
