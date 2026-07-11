#!/usr/bin/env bash
# Hermes Recruiter Agency — end-to-end demo run.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

cd "$ROOT"

# Load .env if present (dotenv also handles this from Python, but exporting helps subshells).
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Reset per-run trace log so demo starts clean
: > "$HERE/traces.jsonl"

echo "== Hermes Recruiter Agency :: demo run =="
echo "root:   $ROOT"
echo "python: $(command -v python3 || command -v python)"
echo "jd:     $HERE/jd.txt"
echo

PY="$(command -v python3 || command -v python)"
exec "$PY" -m hermes.manager --jd "$HERE/jd.txt" "$@"
