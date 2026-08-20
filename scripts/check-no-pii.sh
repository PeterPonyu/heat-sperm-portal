#!/usr/bin/env bash
# check-no-pii.sh — privacy gate for the heat-sperm-portal repository.
#
# Fails (exit 1) if the checked file set contains anything that could carry
# individual donor information. Four independent rules are applied:
#
#   1. path/extension rules  — forbidden file types and forbidden filenames
#   2. content rules         — forbidden column names and identifier patterns
#   3. size rules            — tabular files with more rows than any aggregate
#                              table in this project legitimately has
#   4. directory rules       — forbidden directories anywhere in the tree
#
# Usage:
#   scripts/check-no-pii.sh            # staged files (pre-commit default)
#   scripts/check-no-pii.sh --tracked  # every tracked file
#   scripts/check-no-pii.sh --worktree # every file in the working tree
#
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:---staged}"
MAX_TABULAR_ROWS=1000

# Files that legitimately mention forbidden strings because they define or
# document the rules. Path rules still apply to them.
CONTENT_ALLOWLIST=(
  ".gitignore"
  "scripts/check-no-pii.sh"
  ".githooks/pre-commit"
  "DATA_POLICY.md"
  "CONTRIBUTING.md"
  "README.md"
  "analysis/ANALYSIS_CONTRACT.md"
  "schema/README.md"
  "scripts/build_aggregates.py"
  "scripts/fetch_aggregate_sources.sh"
)

fail=0
note() { printf '%s\n' "$*"; }
violation() { printf 'BLOCKED  %-58s %s\n' "$1" "$2"; fail=1; }

case "$MODE" in
  --staged)
    mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null)
    SCOPE="staged files" ;;
  --tracked)
    mapfile -t FILES < <(git ls-files 2>/dev/null)
    SCOPE="tracked files" ;;
  --worktree)
    mapfile -t FILES < <(find . -type f \
      -not -path './.git/*' -not -path '*/node_modules/*' \
      -not -path '*/.next/*' -not -path '*/out/*' | sed 's|^\./||')
    SCOPE="working-tree files" ;;
  *)
    note "unknown mode: $MODE"; exit 2 ;;
esac

note "check-no-pii: scanning ${#FILES[@]} ${SCOPE}"

# ---------------------------------------------------------------------------
# Rule 1 + 4: forbidden extensions, filenames and directories
# ---------------------------------------------------------------------------
FORBIDDEN_PATH_RE='(\.xlsx?$|\.xlsm$|\.xlsb$|\.h5ad$|\.h5$|\.loom$|\.rds$|\.RData$|(^|/)spermdata/|(^|/)data/raw/|(^|/)raw_data/|harmonized_donor_samples|harmonized_[a-z]+_clinical|donor_exposure|xiamen_exposure|(^|/)\.env)'

for f in "${FILES[@]}"; do
  [ -n "$f" ] || continue
  if printf '%s' "$f" | grep -Eq "$FORBIDDEN_PATH_RE"; then
    violation "$f" "forbidden path / file type"
  fi
done

# ---------------------------------------------------------------------------
# Rule 2: forbidden content
# ---------------------------------------------------------------------------
# Column names and free-text markers that only appear in donor-level data.
PII_COLUMN_RE='(姓名|身份证|身份證|证件号|手机号|手機號|联系电话|聯繫電話|住址|家庭地址|详细地址|詳細地址|供精者姓名|捐精者姓名)'
# donor_id as a real column/field, not as prose inside a documented schema.
DONOR_KEY_RE='(^|[,;"[:space:]])donor_id([,;"[:space:]]|$)'
# Mainland China resident ID (18 char) and mobile number (11 digit).
CN_ID_RE='[1-9][0-9]{5}(19|20)[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[0-9]{3}[0-9Xx]'
CN_MOBILE_RE='(^|[^0-9])1[3-9][0-9]{9}([^0-9]|$)'

is_allowlisted() {
  local target="$1" a
  for a in "${CONTENT_ALLOWLIST[@]}"; do
    [ "$target" = "$a" ] && return 0
  done
  return 1
}

for f in "${FILES[@]}"; do
  [ -n "$f" ] && [ -f "$f" ] || continue
  is_allowlisted "$f" && continue
  # skip binary files
  if ! LC_ALL=C grep -Iq . "$f" 2>/dev/null; then continue; fi

  grep -Eq "$PII_COLUMN_RE"  "$f" 2>/dev/null && violation "$f" "personal-identifier column name"
  grep -Eq "$DONOR_KEY_RE"   "$f" 2>/dev/null && violation "$f" "donor_id field present"
  grep -Eq "$CN_ID_RE"       "$f" 2>/dev/null && violation "$f" "resident-ID-shaped string"
  grep -Eq "$CN_MOBILE_RE"   "$f" 2>/dev/null && violation "$f" "mobile-number-shaped string"
done

# ---------------------------------------------------------------------------
# Rule 3: tabular size ceiling
# ---------------------------------------------------------------------------
for f in "${FILES[@]}"; do
  [ -n "$f" ] && [ -f "$f" ] || continue
  case "$f" in
    *.csv|*.tsv)
      rows=$(wc -l < "$f")
      if [ "$rows" -gt "$MAX_TABULAR_ROWS" ]; then
        violation "$f" "$rows rows > ${MAX_TABULAR_ROWS}-row aggregate ceiling"
      fi ;;
  esac
done

if [ "$fail" -ne 0 ]; then
  note ""
  note "check-no-pii FAILED. Nothing donor-level may enter this repository."
  note "See DATA_POLICY.md. Only aggregate statistics are permitted."
  exit 1
fi

note "check-no-pii PASSED — no forbidden paths, columns, identifiers or oversized tables."
exit 0
