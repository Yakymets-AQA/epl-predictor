#!/usr/bin/env python3
"""Generate/update an Excel standings table from prediction and result files."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd

PREDICTION_COLUMNS = {
    "match_id",
    "round",
    "user",
    "home_team",
    "away_team",
    "predicted_home_goals",
    "predicted_away_goals",
}
RESULT_COLUMNS = {
    "match_id",
    "round",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
}

COLUMN_TRANSLATIONS = {
    "Place": "Місце",
    "User ID": "User ID",
    "Name": "Ім'я",
    "Matches": "Матчі",
    "Exact scores": "Точні прогнози матчів",
    "Total points": "Загальні бали",
    "Avg points per round": "Середня кількість балів за тури",
}
ROUND_METRIC_TRANSLATIONS = {"exact": "Точні прогнози матчів", "points": "бали"}
ROUND_COLUMN_PATTERN = re.compile(r"Round (\d+) (exact|points)$")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PREDICTIONS_PATH = BASE_DIR / "data" / "predictions_sample.csv"
DEFAULT_RESULTS_PATH = BASE_DIR / "data" / "results_sample.csv"
DEFAULT_OUTPUT_PATH = BASE_DIR / "output" / "apl_standings.xlsx"
DEFAULT_SHEET_NAME = "Standings"


class ScoreComputationError(Exception):
    """Raised when we cannot compute a standings table."""


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        sep = "\t" if suffix == ".txt" else ","
        return pd.read_csv(path, sep=sep)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ScoreComputationError(f"Unsupported file type: {path.suffix}")


def _ensure_columns(df: pd.DataFrame, required: Iterable[str], label: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ScoreComputationError(
            f"{label} is missing required columns: {', '.join(missing)}"
        )


def _coerce_int_column(df: pd.DataFrame, column: str, label: str) -> None:
    series = pd.to_numeric(df[column], errors="coerce")
    invalid_mask = series.isna()
    if invalid_mask.any():
        sample = df.loc[invalid_mask, column].astype(str).head(3).tolist()
        raise ScoreComputationError(
            f"{label} has non-numeric values in '{column}': {', '.join(sample)}"
        )
    non_integer_mask = (series % 1) != 0
    if non_integer_mask.any():
        sample = df.loc[non_integer_mask, column].astype(str).head(3).tolist()
        raise ScoreComputationError(
            f"{label} has non-integer values in '{column}': {', '.join(sample)}"
        )
    df[column] = series.astype(int)


def _winner_sign(diff: int) -> str:
    if diff > 0:
        return "H"
    if diff < 0:
        return "A"
    return "D"


def _load_inputs(pred_path: Path, result_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    predictions = _read_table(pred_path)
    results = _read_table(result_path)
    _ensure_columns(predictions, PREDICTION_COLUMNS, "Prediction file")
    _ensure_columns(results, RESULT_COLUMNS, "Result file")
    return predictions, results


def _score_predictions(predictions: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    predictions = predictions.copy()
    results = results.copy()
    participant_cols = ["user_id", "user"] if "user_id" in predictions.columns else ["user"]
    all_participants = (
        predictions[participant_cols].drop_duplicates()
        if not predictions.empty
        else pd.DataFrame(columns=participant_cols)
    )

    predictions.rename(
        columns={
            "round": "round_pred",
            "home_team": "home_team_pred",
            "away_team": "away_team_pred",
        },
        inplace=True,
    )
    merged = predictions.merge(results, on="match_id", how="left", suffixes=("_pred", "_act"))

    missing_mask = merged["home_goals"].isna() | merged["away_goals"].isna()
    if missing_mask.any():
        missing_matches = merged.loc[missing_mask, "match_id"].unique()
        print(
            "[WARNING] Dropping predictions for matches without results: "
            + ", ".join(map(str, missing_matches)),
            file=sys.stderr,
        )
        merged = merged.loc[~missing_mask].copy()
    matched_participants = (
        merged[participant_cols].drop_duplicates()
        if not merged.empty
        else pd.DataFrame(columns=participant_cols)
    )
    if merged.empty and all_participants.empty:
        raise ScoreComputationError("No predictions could be matched with results.")

    merged["round"] = merged["round"].fillna(merged["round_pred"])
    merged["home_team"] = merged["home_team"].fillna(merged["home_team_pred"])
    merged["away_team"] = merged["away_team"].fillna(merged["away_team_pred"])

    for col in [
        "predicted_home_goals",
        "predicted_away_goals",
        "home_goals",
        "away_goals",
    ]:
        _coerce_int_column(merged, col, "Merged data")
    _coerce_int_column(merged, "round", "Merged data")

    merged["actual_diff"] = merged["home_goals"] - merged["away_goals"]
    merged["predicted_diff"] = merged["predicted_home_goals"] - merged["predicted_away_goals"]
    merged["actual_winner"] = merged["actual_diff"].apply(_winner_sign)
    merged["predicted_winner"] = merged["predicted_diff"].apply(_winner_sign)

    merged["is_exact"] = (
        (merged["predicted_home_goals"] == merged["home_goals"]) &
        (merged["predicted_away_goals"] == merged["away_goals"])
    )
    merged["has_winner"] = merged["predicted_winner"] == merged["actual_winner"]
    merged["has_diff"] = merged["predicted_diff"] == merged["actual_diff"]

    def _row_points(row: pd.Series) -> int:
        if row["is_exact"]:
            return 4
        if row["has_winner"] and row["has_diff"]:
            return 2
        if row["has_winner"]:
            return 1
        return 0

    merged["points"] = merged.apply(_row_points, axis=1)

    missing_participants = pd.DataFrame()
    if not all_participants.empty:
        merged_part = matched_participants if not matched_participants.empty else pd.DataFrame(columns=participant_cols)
        missing_participants = (
            all_participants.merge(
                merged_part,
                on=participant_cols,
                how="left",
                indicator=True,
            )
            .loc[lambda df: df["_merge"] == "left_only"]
            .drop(columns="_merge")
        )
    if not missing_participants.empty:
        default_values = {
            "match_id": pd.NA,
            "round_pred": pd.NA,
            "home_team_pred": "",
            "away_team_pred": "",
            "predicted_home_goals": 0,
            "predicted_away_goals": 0,
            "home_goals": 0,
            "away_goals": 0,
            "round": pd.NA,
            "home_team": "",
            "away_team": "",
            "actual_diff": 0,
            "predicted_diff": 0,
            "actual_winner": "",
            "predicted_winner": "",
            "is_exact": False,
            "has_winner": False,
            "has_diff": False,
            "points": 0,
        }
        placeholder_rows = []
        for _, part in missing_participants.iterrows():
            entry = {col: default_values.get(col, 0) for col in merged.columns}
            for col in participant_cols:
                entry[col] = part[col]
            placeholder_rows.append(entry)
        merged = pd.concat([merged, pd.DataFrame(placeholder_rows)], ignore_index=True, sort=False)

    return merged


def _build_standings(scored: pd.DataFrame) -> pd.DataFrame:
    use_user_id = "user_id" in scored.columns
    participant_cols = ["user_id", "user"] if use_user_id else ["user"]

    per_user = (
        scored.groupby(participant_cols)
        .agg(
            predictions=("match_id", "count"),
            total_points=("points", "sum"),
            exact_scores=("is_exact", "sum"),
            rounds_played=("round", "nunique"),
        )
        .reset_index()
    )
    per_user["avg_points_per_round"] = (
        per_user["total_points"] / per_user["rounds_played"].clip(lower=1)
    ).round(2)

    per_round = (
        scored.groupby(participant_cols + ["round"])
        .agg(round_points=("points", "sum"), round_exact=("is_exact", "sum"))
        .reset_index()
    )
    rounds = sorted(per_round["round"].unique())

    sort_by = ["total_points", "exact_scores", "avg_points_per_round"]
    ascending = [False, False, False]
    if use_user_id:
        sort_by.extend(["user_id", "user"])
        ascending.extend([True, True])
    else:
        sort_by.append("user")
        ascending.append(True)

    standings = per_user.sort_values(by=sort_by, ascending=ascending).reset_index(drop=True)
    standings.insert(0, "Place", range(1, len(standings) + 1))
    standings.rename(
        columns={
            "user": "Name",
            "predictions": "Matches",
            "total_points": "Total points",
            "exact_scores": "Exact scores",
            "avg_points_per_round": "Avg points per round",
        },
        inplace=True,
    )
    if use_user_id:
        standings.rename(columns={"user_id": "User ID"}, inplace=True)
    standings.drop(columns=["rounds_played"], inplace=True)

    round_lookup = {
        rnd: grp.set_index(participant_cols)
        for rnd, grp in per_round.groupby("round")
    }

    key_column = "_participant_key"
    if use_user_id:
        standings[key_column] = list(zip(standings["User ID"], standings["Name"]))
    else:
        standings[key_column] = standings["Name"]
    for rnd in rounds:
        exact_series = round_lookup[rnd]["round_exact"] if rnd in round_lookup else None
        point_series = round_lookup[rnd]["round_points"] if rnd in round_lookup else None
        exact_map = exact_series.to_dict() if exact_series is not None else {}
        point_map = point_series.to_dict() if point_series is not None else {}
        standings[f"Round {rnd} exact"] = (
            standings[key_column].map(exact_map).fillna(0).astype(int)
        )
        standings[f"Round {rnd} points"] = (
            standings[key_column].map(point_map).fillna(0).astype(int)
        )

    standings.drop(columns=[key_column], inplace=True)

    column_order = ["Place", "Name", "Matches", "Exact scores", "Total points", "Avg points per round"]
    if use_user_id:
        column_order.insert(1, "User ID")
    round_columns = [
        col for col in standings.columns if col not in column_order
    ]
    ordered = standings[column_order + round_columns].copy()
    ordered.rename(columns=COLUMN_TRANSLATIONS, inplace=True)

    def _translate_round_column(name: str) -> str:
        match = ROUND_COLUMN_PATTERN.match(name)
        if not match:
            return name
        round_num, metric = match.groups()
        metric_label = ROUND_METRIC_TRANSLATIONS.get(metric, metric)
        return f"Тур {round_num} {metric_label}"

    ordered.columns = [_translate_round_column(col) for col in ordered.columns]
    return ordered


def _write_excel(df: pd.DataFrame, output: Path, sheet_name: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if output.exists() else "w"
    writer_kwargs = {"engine": "openpyxl", "mode": mode}
    if mode == "a":
        writer_kwargs["if_sheet_exists"] = "replace"
    with pd.ExcelWriter(output, **writer_kwargs) as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare predictions with real results and produce an Excel standings table."
        )
    )
    parser.add_argument(
        "predictions",
        nargs="?",
        default=DEFAULT_PREDICTIONS_PATH,
        type=Path,
        help="Path to the predictions CSV/XLSX file (default: data/predictions_sample.csv)",
    )
    parser.add_argument(
        "results",
        nargs="?",
        default=DEFAULT_RESULTS_PATH,
        type=Path,
        help="Path to the real results CSV/XLSX file (default: data/results_sample.csv)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=DEFAULT_OUTPUT_PATH,
        type=Path,
        help="Path to the Excel file that should be created or updated",
    )
    parser.add_argument(
        "--sheet",
        default=DEFAULT_SHEET_NAME,
        help="Name of the sheet to create/replace in the output workbook",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    pred_path = args.predictions if isinstance(args.predictions, Path) else Path(args.predictions)
    result_path = args.results if isinstance(args.results, Path) else Path(args.results)
    output_path = args.output if isinstance(args.output, Path) else Path(args.output)

    try:
        predictions, results = _load_inputs(pred_path, result_path)
        scored = _score_predictions(predictions, results)
        standings = _build_standings(scored)
        _write_excel(standings, output_path, args.sheet)
    except ScoreComputationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote standings for {len(standings)} participants to {output_path} (sheet '{args.sheet}')."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
