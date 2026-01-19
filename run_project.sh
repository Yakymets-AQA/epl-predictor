#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PYTHON_CMD="python3"
if [[ -x "${SCRIPT_DIR}/.venv/bin/python" ]]; then
  PYTHON_CMD="${SCRIPT_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Python 3 not found. Create .venv or install Python." >&2
  exit 1
fi

ROUND=${1:-}
if [[ -z "${ROUND}" ]]; then
  echo "Usage: $0 <round-number>" >&2
  exit 1
fi

RAW_RESULTS="data/raw_results_template.txt"
RESULTS_CSV="data/results_sample.csv"
RAW_PREDICTIONS="data/raw_predictions_template.txt"
PREDICTIONS_CSV="data/predictions_sample.csv"
OUTPUT_XLSX="output/apl_standings.xlsx"

"${PYTHON_CMD}" scripts/normalize_text_matches.py "${RAW_RESULTS}"

"${PYTHON_CMD}" scripts/import_text_results.py \
  "${RAW_RESULTS}" \
  "${RESULTS_CSV}" \
  --round "${ROUND}"

"${PYTHON_CMD}" scripts/normalize_text_matches.py "${RAW_PREDICTIONS}"

"${PYTHON_CMD}" scripts/import_text_predictions.py \
  "${RAW_PREDICTIONS}" \
  "${RESULTS_CSV}" \
  "${PREDICTIONS_CSV}" \
  --clear-users

"${PYTHON_CMD}" scripts/generate_scoreboard.py \
  "${PREDICTIONS_CSV}" \
  "${RESULTS_CSV}" \
  "${OUTPUT_XLSX}"
