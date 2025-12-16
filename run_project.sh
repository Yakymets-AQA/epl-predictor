#!/usr/bin/env bash
set -euo pipefail

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

python3 scripts/normalize_text_matches.py "${RAW_RESULTS}"

python3 scripts/import_text_results.py \
  "${RAW_RESULTS}" \
  "${RESULTS_CSV}" \
  --round "${ROUND}"

python3 scripts/normalize_text_matches.py "${RAW_PREDICTIONS}"

python3 scripts/import_text_predictions.py \
  "${RAW_PREDICTIONS}" \
  "${RESULTS_CSV}" \
  "${PREDICTIONS_CSV}" \
  --clear-users

python3 scripts/generate_scoreboard.py \
  "${PREDICTIONS_CSV}" \
  "${RESULTS_CSV}" \
  "${OUTPUT_XLSX}"
