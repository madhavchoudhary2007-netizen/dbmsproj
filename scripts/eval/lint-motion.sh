#!/usr/bin/env bash
# Motion lint (check A-7, static part). Exit 1 on any hit, 2 if no source directory exists.
set -u

if [[ ${1:-} == --self-test ]]; then
  [[ $# == 1 ]] || { echo "usage: lint-motion.sh --self-test" >&2; exit 2; }
  python3 -m scripts.eval.neo_motion --self-test
  exit $?
fi

if (($#)); then
  targets=("$@")
else
  . "$(dirname "$0")/_dirs.sh"
  read -r -a targets <<< "$dirs"
fi
if ((${#targets[@]} == 0)); then
  echo "LINT ERROR: no source paths supplied" >&2
  exit 2
fi

bad=0
if rg -nP '^(?!\s*/\*.*\*/\s*$).*?(?:transition:\s*all\b|transition-all)' "${targets[@]}"; then
  echo "BANNED: transition: all"
  bad=1
fi
if rg -nP '^(?!\s*/\*.*\*/\s*$).*?transition(-property)?:[^;]*\b(width|height|top|left|margin|box-shadow)\b' "${targets[@]}"; then
  echo "BANNED: animating layout or shadow properties"
  bad=1
fi
if rg -qP "transition|animation|@keyframes" "${targets[@]}" && ! rg -q "prefers-reduced-motion" "${targets[@]}"; then
  echo "MISSING: no prefers-reduced-motion guard found"
  bad=1
fi

css_files=()
for target in "${targets[@]}"; do
  if [[ -f $target ]]; then
    case "/$target/" in
      */vendor/*|*/build/*|*/dist/*|*/coverage/*|*/generated/*|*/node_modules/*|*/.next/*|*/.git/*) ;;
      *) [[ $target == *.css ]] && css_files+=("$target") ;;
    esac
  elif [[ -d $target ]]; then
    while IFS= read -r -d '' file; do css_files+=("$file"); done < <(
      find "$target" \( -type d \( -name .git -o -name vendor -o -name build -o -name dist \
        -o -name coverage -o -name generated -o -name node_modules -o -name .next \) -prune \) \
        -o -type f -name '*.css' -print0
    )
  else
    echo "LINT ERROR: source path does not exist: $target" >&2
    bad=1
  fi
done

for file in "${css_files[@]}"; do
  if ! python3 - "$file" <<'PY'
import sys
from pathlib import Path

from scripts.eval.neo_motion import check_motion

path = Path(sys.argv[1])
text = path.read_text()
errors = check_motion(text, css=True)
for offset, message in errors:
    line = text.count("\n", 0, offset) + 1
    print(f"{path}:{line}: {message}")
raise SystemExit(bool(errors))
PY
  then
    bad=1
  fi
done

exit "$bad"
