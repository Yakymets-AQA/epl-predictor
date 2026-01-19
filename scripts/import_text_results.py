#!/usr/bin/env python3
"""Convert a plain-text list of matches into rows inside results_sample.csv."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from text_match_parser import parse_match_line
from team_aliases import normalize_team_name

RESULT_COLUMNS: Sequence[str] = (
    "match_id",
    "round",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
)


def _parse_matches(lines: Iterable[str]) -> List[dict]:
    """Extract match data from text lines."""
    matches: List[dict] = []
    skipped: List[str] = []
    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        parsed = parse_match_line(line)
        if not parsed:
            skipped.append(line)
            continue
        matches.append(parsed)
    if skipped:
        print(
            f"[INFO] Skipped {len(skipped)} non-match lines: {', '.join(skipped[:3])}"
            + ("..." if len(skipped) > 3 else ""),
            file=sys.stderr,
        )
    if not matches:
        raise SystemExit("No matches were found in the provided text file.")
    return matches


def _normalize_team(name: str) -> str:
    return normalize_team_name(name)


def _match_key(round_value: str | int, home_team: str, away_team: str) -> Tuple[str, str, str]:
    round_key = str(round_value).strip()
    return (round_key, _normalize_team(home_team), _normalize_team(away_team))


def _load_existing(path: Path) -> List[dict]:
    """Return existing result rows (or an empty list when the file is missing)."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)
    return rows


def _index_existing(rows: List[dict]) -> dict[Tuple[str, str, str], dict]:
    index: dict[Tuple[str, str, str], dict] = {}
    for row in rows:
        key = _match_key(
            row.get("round", ""),
            row.get("home_team", ""),
            row.get("away_team", ""),
        )
        if key not in index:
            index[key] = row
    return index


def _next_match_number(existing_rows: List[dict], prefix: str) -> int:
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    max_number = 0
    for row in existing_rows:
        match_id = row.get("match_id", "")
        match = pattern.match(match_id)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number


def _write_results(path: Path, rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append matches described in a text file to a results CSV."
    )
    parser.add_argument("text_file", type=Path, help="Plain-text file with match lines.")
    parser.add_argument(
        "results_csv",
        type=Path,
        help="CSV file to create/update (e.g., data/results_sample.csv).",
    )
    parser.add_argument(
        "--round",
        type=int,
        required=True,
        help="Round number that should be assigned to every imported match.",
    )
    parser.add_argument(
        "--match-prefix",
        default="M",
        help="Prefix to use for generated match_id values (default: M).",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    text_lines = args.text_file.read_text(encoding="utf-8").splitlines()
    parsed_matches = _parse_matches(text_lines)

    existing_rows = _load_existing(args.results_csv)
    existing_index = _index_existing(existing_rows)
    next_match_number = _next_match_number(existing_rows, args.match_prefix)

    new_rows = []
    new_keys = set()
    for match in parsed_matches:
        key = _match_key(args.round, match["home_team"], match["away_team"])
        if key in new_keys:
            continue
        new_keys.add(key)
        existing_row = existing_index.get(key)
        match_id = (existing_row or {}).get("match_id", "")
        if not match_id:
            next_match_number += 1
            match_id = f"{args.match_prefix}{next_match_number}"
        new_rows.append(
            {
                "match_id": match_id,
                "round": str(args.round),
                "home_team": match["home_team"],
                "away_team": match["away_team"],
                "home_goals": match["home_goals"],
                "away_goals": match["away_goals"],
            }
        )

    kept_rows = []
    if new_keys:
        for row in existing_rows:
            key = _match_key(
                row.get("round", ""),
                row.get("home_team", ""),
                row.get("away_team", ""),
            )
            if key in new_keys:
                continue
            kept_rows.append(row)
    else:
        kept_rows = existing_rows
    all_rows = kept_rows + new_rows
    _write_results(args.results_csv, all_rows)

    print(f"Imported {len(new_rows)} matches into {args.results_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
