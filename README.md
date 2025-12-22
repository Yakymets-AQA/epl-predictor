# EPL predictor helper

This repository contains a small utility that reads a table with users' match predictions,
compares it with the actual match results and produces an Excel standings sheet that looks
like the sample on the screenshot from the request. Every participant receives points per
match according to the rules:

1. 4 points — guessed the full score (both teams goals).
2. 2 points — guessed the winner and the goal difference but not the exact score.
3. 1 point — guessed only the winner (or a draw).

The standings sheet lists the overall totals (place, user name, number of predictions,
exact scores, total points, average per round) and then adds two columns per round:
`Round N exact` and `Round N points`. You can edit the column names in the script if you
want to localize the table — only ASCII is used by default.

## Project layout

```
├── data
│   ├── predictions_sample.csv
│   ├── results_sample.csv
│   ├── raw_results_template.txt
│   └── raw_predictions_template.txt
├── output
│   └── apl_standings.xlsx        # created after you run the script once
├── requirements.txt
└── scripts
    ├── generate_scoreboard.py
    ├── import_text_results.py
    ├── import_text_predictions.py
    └── update_from_text.py
```

## Input files

Both the prediction file and the results file can be in CSV/TSV/XLS/XLSX format. The
script detects the format by extension and expects the following column names:

### Predictions

| column | description |
| --- | --- |
| `match_id` | Identifier that matches the results table. |
| `round` | Tour/round identifier (integer). |
| `user_id` | Optional stable identifier for a participant (used together with `user`). |
| `user` | Participant name. |
| `home_team`, `away_team` | Optional metadata (used only if the results file misses them). |
| `predicted_home_goals`, `predicted_away_goals` | Integer score prediction. |

### Results

| column | description |
| --- | --- |
| `match_id` | Identifier that matches the prediction table. |
| `round` | Tour id (integer). |
| `home_team`, `away_team` | Team names. |
| `home_goals`, `away_goals` | Real match score. |

Add as many rows/users as you need — the scoring logic is data-driven.

## Install dependencies

```bash
cd epl-predictor
python3 -m pip install -r requirements.txt
```

(pandas and openpyxl are already installed in many Python environments; skip the command
if you already have them.)

## Run the script

```bash
python3 scripts/generate_scoreboard.py \
  data/predictions_sample.csv \
  data/results_sample.csv \
  output/apl_standings.xlsx
```

Or use the helper that also imports the template text files:

```bash
./run_project.sh <round-number>
```

The script reads `data/raw_results_template.txt` and `data/raw_predictions_template.txt`,
imports their contents into `data/results_sample.csv` / `data/predictions_sample.csv`
(replacing predictions for the listed fixtures) and finally rebuilds
`output/apl_standings.xlsx`.



