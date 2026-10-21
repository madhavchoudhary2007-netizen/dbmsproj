# shellcheck shell=bash
[ -f .agent/commands.env ] && . .agent/commands.env
dirs=""; for d in ${SRC_DIRS:-src app lib components}; do [ -d "$d" ] && dirs="$dirs $d"; done
[ -n "$dirs" ] || { echo "LINT ERROR: none of the SRC_DIRS exist (${SRC_DIRS:-src app lib components}); set SRC_DIRS in .agent/commands.env" >&2; exit 2; }
