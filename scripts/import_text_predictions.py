#!/usr/bin/env python3
"""Convert plain-text user predictions into the structured predictions CSV."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from text_match_parser import parse_match_line
from team_aliases import normalize_team_name

PREDICTION_COLUMNS: Sequence[str] = (
    "match_id",
    "round",
    "user_id",
    "user",
    "home_team",
    "away_team",
    "predicted_home_goals",
    "predicted_away_goals",
)

USER_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*\d+[A-Za-z0-9_-]*$")
GENERATED_ID_PATTERN = re.compile(r"^U(\d+)$")


def _normalize_team(name: str) -> str:
    return normalize_team_name(name)


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _contains_letters(text: str) -> bool:
    return any(ch.isalpha() for ch in text)


def _load_results(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Results file {path} was not found.")
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        data = list(reader)
    if not data:
        raise SystemExit(f"Results file {path} is empty.")
    mapping: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in data:
        key = (_normalize_team(row["home_team"]), _normalize_team(row["away_team"]))
        mapping[key] = row
    return mapping


def _split_blocks(lines: Iterable[str]) -> List[Tuple[List[str], List[str]]]:
    blocks: List[Tuple[List[str], List[str]]] = []
    metadata: List[str] = []
    matches: List[str] = []

    def _flush() -> None:
        nonlocal metadata, matches
        if matches:
            blocks.append((metadata, matches))
            metadata = []
            matches = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            if not stripped:
                _flush()
            continue
        parsed = parse_match_line(stripped)
        if parsed:
            matches.append(stripped)
            continue
        if matches:
            _flush()
        metadata.append(stripped)
    _flush()
    return blocks


def _extract_user_info(meta: List[str], idx: int) -> Tuple[str | None, str]:
    user_id = next((item for item in meta if USER_ID_PATTERN.match(item)), None)
    name_candidate = next(
        (item for item in reversed(meta) if _contains_letters(item) and item != user_id),
        None,
    )
    if name_candidate:
        user_name = name_candidate.strip()
    elif user_id:
        user_name = user_id
    else:
        user_name = f"User {idx + 1}"
    return user_id, user_name


def _load_existing_predictions(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)
    for row in rows:
        row.setdefault("user_id", "")
    return rows


def _next_generated_user_id(existing_rows: List[dict]) -> int:
    max_id = 0
    for row in existing_rows:
        uid = (row.get("user_id") or "").strip()
        match = GENERATED_ID_PATTERN.match(uid)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id + 1


def _write_predictions(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=PREDICTION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row_key_from_values(user_id: str, user: str, match_id: str) -> Tuple[str, str, str]:
    user_id_norm = (user_id or "").strip().lower()
    user_norm = (user or "").strip().lower()
    match_norm = (match_id or "").strip().lower()
    if user_id_norm:
        return ("id", user_id_norm, match_norm)
    return ("name", user_norm, match_norm)


def _merge_prediction_rows(
    existing_rows: List[dict],
    new_rows: List[dict],
    clear_matches: bool,
) -> List[dict]:
    from collections import OrderedDict

    def _row_key(row: dict) -> Tuple[str, str, str]:
        return _row_key_from_values(row.get("user_id", ""), row.get("user", ""), row.get("match_id", ""))

    merged = OrderedDict()
    for row in existing_rows:
        merged[_row_key(row)] = row

    if clear_matches:
        keys_to_remove = {_row_key(row) for row in new_rows}
        for key in keys_to_remove:
            merged.pop(key, None)

    for row in new_rows:
        merged[_row_key(row)] = row
    return list(merged.values())


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append user predictions from a text file to the predictions CSV."
    )
    parser.add_argument(
        "text_file",
        type=Path,
        help="Text file that contains blocks per user (metadata + match lines).",
    )
    parser.add_argument(
        "results_csv",
        type=Path,
        help="CSV with real results (used to map teams to match_id).",
    )
    parser.add_argument(
        "predictions_csv",
        type=Path,
        help="CSV to create/update with parsed predictions.",
    )
    parser.add_argument(
        "--round",
        type=int,
        help="Override the round number for all imported matches (default: use results file).",
    )
    parser.add_argument(
        "--clear-users",
        action="store_true",
        help="Replace previous predictions for the same users and fixtures (other rounds stay intact).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    text_lines = args.text_file.read_text(encoding="utf-8").splitlines()
    blocks = _split_blocks(text_lines)
    if not blocks:
        print("No predictions found in the provided text file.", file=sys.stderr)
        return 1

    results_map = _load_results(args.results_csv)
    existing_rows = _load_existing_predictions(args.predictions_csv)

    next_user_id = _next_generated_user_id(existing_rows)
    name_to_id: Dict[str, str] = {}
    for row in existing_rows:
        normalized_name = _normalize_name(row.get("user", ""))
        uid = (row.get("user_id") or "").strip()
        if normalized_name and uid:
            name_to_id[normalized_name] = uid

    new_rows: List[dict] = []

    skipped_matches: List[str] = []
    for idx, (meta, match_lines) in enumerate(blocks, start=1):
        parsed_matches = [parse_match_line(line) for line in match_lines]
        parsed_matches = [match for match in parsed_matches if match]
        if not parsed_matches:
            continue
        user_id, user_name = _extract_user_info(meta, idx)
        normalized_name = _normalize_name(user_name)
        if not user_id:
            if normalized_name and normalized_name in name_to_id:
                user_id = name_to_id[normalized_name]
            else:
                user_id = f"U{next_user_id:04d}"
                next_user_id += 1
                if normalized_name:
                    name_to_id[normalized_name] = user_id
        elif normalized_name and normalized_name not in name_to_id:
            name_to_id[normalized_name] = user_id
        for match in parsed_matches:
            key = (_normalize_team(match["home_team"]), _normalize_team(match["away_team"]))
            result_row = results_map.get(key)
            if not result_row:
                skipped_matches.append(match["home_team"] + " vs " + match["away_team"])
                continue
            round_value = args.round if args.round is not None else result_row["round"]
            new_rows.append(
                {
                    "match_id": result_row["match_id"],
                    "round": str(round_value),
                    "user_id": user_id or "",
                    "user": user_name,
                    "home_team": result_row["home_team"],
                    "away_team": result_row["away_team"],
                    "predicted_home_goals": match["home_goals"],
                    "predicted_away_goals": match["away_goals"],
                }
            )

    if not new_rows:
        print("Could not match any lines with the known fixtures.", file=sys.stderr)
        return 1

    combined = _merge_prediction_rows(existing_rows, new_rows, args.clear_users)
    _write_predictions(args.predictions_csv, combined)

    print(f"Imported {len(new_rows)} predictions into {args.predictions_csv}")
    if skipped_matches:
        print(
            "[WARNING] Skipped matches without a matching fixture: "
            + ", ".join(sorted(set(skipped_matches))),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
