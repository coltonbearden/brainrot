#!/usr/bin/env bash
# Package each skill as an individually uploadable claude.ai zip (dist/<skill>.zip,
# with <skill>/SKILL.md at the zip root — the layout Settings > Capabilities > Skills expects).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILLS="$HERE/../skills"
DIST="$HERE/../../../dist"
mkdir -p "$DIST"
for d in "$SKILLS"/*/; do
  name="$(basename "$d")"
  rm -f "$DIST/$name.zip"
  (cd "$SKILLS" && zip -qr "$DIST/$name.zip" "$name")
  echo "dist/$name.zip"
done
