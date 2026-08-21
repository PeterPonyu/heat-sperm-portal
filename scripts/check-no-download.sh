#!/usr/bin/env bash
# Fail if CI or repo scripts fetch datasets. npm/Node registry is allowed.
# Does not itself download anything.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0
# Hosts / path tokens that would pull analysis data or donor files.
FORBIDDEN_RE='(huggingface\.co|hf\.co|hf-mirror|zenodo\.org|figshare\.com|osf\.io|drive\.google|docs\.google|dropbox\.com|spermdata|ncbi\.nlm\.nih\.gov/geo|eutils\.ncbi|cdn-lfs|xethub\.hf\.co|openalex\.org/download)'

# Gate scripts name the banned hosts so they can reject them.
ALLOWLIST=(
  "scripts/check-no-download.sh"
  "scripts/check-no-pii.sh"
)

is_allowlisted() {
  local target="$1" a
  for a in "${ALLOWLIST[@]}"; do
    [ "$target" = "$a" ] && return 0
  done
  return 1
}

scan() {
  local f="$1"
  [ -f "$f" ] || return 0
  is_allowlisted "$f" && return 0
  if grep -Eiq "$FORBIDDEN_RE" "$f"; then
    printf 'BLOCKED  %s  dataset-download token\n' "$f"
    fail=1
  fi
}

while IFS= read -r f; do
  scan "$f"
done < <(find .github/workflows scripts -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.sh' -o -name '*.py' \) | sed 's|^\./||')

# Workflows must not curl/wget arbitrary URLs except GitHub Actions tooling.
while IFS= read -r f; do
  if grep -Eiq '(curl |wget )' "$f"; then
    printf 'BLOCKED  %s  curl/wget in workflow (no dataset fetch)\n' "$f"
    fail=1
  fi
done < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) 2>/dev/null)

if [ "$fail" -ne 0 ]; then
  echo "check-no-download FAILED"
  exit 1
fi
echo "check-no-download PASS — no dataset fetchers in workflows/scripts."
