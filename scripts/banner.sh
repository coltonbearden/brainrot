#!/usr/bin/env bash
# brainrot — say hello to the mascot.
#
# Usage: banner.sh [--small] [--plain] [--help]
#   --small   compact 10-column mascot (narrow terminals)
#   --plain   never emit ANSI color
#
# Color is also disabled automatically when stdout is not a TTY or NO_COLOR is
# set, so CI logs stay clean. Pure ASCII: no Unicode, renders in any terminal.
set -euo pipefail

SMALL=0
PLAIN=0
for arg in "$@"; do
  case "$arg" in
    --small) SMALL=1 ;;
    --plain) PLAIN=1 ;;
    -h|--help)
      sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) printf 'banner.sh: unknown option %s\n' "$arg" >&2; exit 2 ;;
  esac
done

if [[ -t 1 && -z "${NO_COLOR:-}" && "$PLAIN" -eq 0 ]]; then
  SPORE=$'\033[38;5;190m'
  LIVE=$'\033[38;5;40m'
  ROT=$'\033[38;5;28m'
  DIM=$'\033[38;5;242m'
  BOLD=$'\033[1m'
  OFF=$'\033[0m'
else
  SPORE=''; LIVE=''; ROT=''; DIM=''; BOLD=''; OFF=''
fi

if [[ "$SMALL" -eq 1 ]]; then
  SPORE_ART=(
    "    **  **"
  )
  BODY_ART=(
    "  ##########"
    "  ##      ##"
    "  ## ##  # ##"
    "  ##########"
    "  ##  ##  ##"
    "  ##  ##  ##"
    "  ##      ##"
  )
else
  SPORE_ART=(
    "          **    **"
    "        ******  ****"
  )
  BODY_ART=(
    "    ########################"
    "    ############::::########"
    "    ##    ############  ####"
    "    ##    ############  ####"
    "############################"
    "################################"
    "    ############################"
    "    ##  ##  ##  ##  ########"
    "    ####::::################"
    "    ####    ####      ####"
    "    ####    ####      ####"
    "    ####              ####"
    "    ####"
  )
fi

printf '\n'
for line in "${SPORE_ART[@]}"; do printf '%s%s%s\n' "$SPORE" "$line" "$OFF"; done
for line in "${BODY_ART[@]}"; do printf '%s%s%s\n' "$LIVE" "$line" "$OFF"; done
printf '\n'
printf '  %s%sbrainrot%s %s- a self-audit toolkit for Claude%s\n' "$BOLD" "$LIVE" "$OFF" "$DIM" "$OFF"
printf '  %s10 skills . 2 commands . read-only until you approve the write%s\n' "$ROT" "$OFF"
printf '\n'
