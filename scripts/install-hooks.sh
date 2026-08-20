#!/usr/bin/env bash
# Copy the tracked hook into .git/hooks/. Do not set core.hooksPath.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
chmod +x .githooks/pre-commit scripts/check-no-pii.sh
mkdir -p .git/hooks
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "installed .git/hooks/pre-commit"
echo "pre-commit gate active: scripts/check-no-pii.sh --staged"
