#!/usr/bin/env python3
"""Run the text importer and standings generator in one command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

import generate_scoreboard
import import_text_predictions
import import_text_results


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import text results and refresh the standings workbook."
    )
    parser.add_argument(
        "text_file",
        type=Path,
        help="Plain-text file with lines like 'Team 1 1 : 2 Team 2'.",
    )
    parser.add_argument(
        "--round",
        type=int,
        required=True,
        help="Round number to assign to all imported matches.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("data/predictions_sample.csv"),
        help="Prediction file to score (default: data/predictions_sample.csv).",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("data/results_sample.csv"),
        help="Results CSV to append to (default: data/results_sample.csv).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/apl_standings.xlsx"),
        help="Excel file to create/update (default: output/apl_standings.xlsx).",
    )
    parser.add_argument(
        "--sheet",
        default="Standings",
        help="Sheet name for the standings workbook (default: Standings).",
    )
    parser.add_argument(
        "--match-prefix",
        default="M",
        help="Prefix for generated match_id values (default: M).",
    )
    parser.add_argument(
        "--predictions-text",
        type=Path,
        help="Optional text file with user predictions to import before scoring.",
    )
    parser.add_argument(
        "--predictions-round",
        type=int,
        help="Override the round number for imported predictions (default: use results file).",
    )
    parser.add_argument(
        "--clear-predictions",
        action="store_true",
        help="Replace existing predictions for the same users and fixtures (older rounds remain).",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _build_import_args(args: argparse.Namespace) -> List[str]:
    cmd = [
        str(args.text_file),
        str(args.results),
        "--round",
        str(args.round),
    ]
    if args.match_prefix != "M":
        cmd.extend(["--match-prefix", args.match_prefix])
    return cmd


def _build_scoreboard_args(args: argparse.Namespace) -> List[str]:
    cmd = [
        str(args.predictions),
        str(args.results),
        str(args.output),
    ]
    if args.sheet != "Standings":
        cmd.extend(["--sheet", args.sheet])
    return cmd


def _build_prediction_args(args: argparse.Namespace) -> List[str]:
    cmd = [
        str(args.predictions_text),
        str(args.results),
        str(args.predictions),
    ]
    if args.predictions_round is not None:
        cmd.extend(["--round", str(args.predictions_round)])
    if args.clear_predictions:
        cmd.append("--clear-users")
    return cmd


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    print(f"[INFO] Importing results from {args.text_file} into {args.results}...")
    import_rc = import_text_results.main(_build_import_args(args))
    if import_rc != 0:
        return import_rc

    if args.predictions_text:
        print(
            f"[INFO] Importing predictions from {args.predictions_text} into {args.predictions}..."
        )
        pred_rc = import_text_predictions.main(_build_prediction_args(args))
        if pred_rc != 0:
            return pred_rc

    print(f"[INFO] Rebuilding standings in {args.output}...")
    score_rc = generate_scoreboard.main(_build_scoreboard_args(args))
    return score_rc


if __name__ == "__main__":
    raise SystemExit(main())
