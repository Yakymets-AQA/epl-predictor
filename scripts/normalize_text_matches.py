#!/usr/bin/env python3
"""Normalize plain-text prediction/result files to a single line format."""
from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path
from typing import Iterable, List, Tuple

from text_match_parser import INVISIBLE_CHARACTERS, format_match_line, parse_match_line

_REMOVE_INVISIBLE = str.maketrans("", "", INVISIBLE_CHARACTERS)


def _normalize_unicode(text: str) -> str:
    """Normalize text to NFC and convert line endings to LF."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", text)


def _normalize_non_match_line(line: str) -> str:
    """Trim metadata/comment lines and strip invisible characters."""
    cleaned = line.replace("\xa0", " ").translate(_REMOVE_INVISIBLE)
    return cleaned.strip()


def _normalize_lines(lines: Iterable[str]) -> Tuple[List[str], int, int]:
    """Return normalized lines, number of changed lines, and match count."""
    normalized: List[str] = []
    changed = 0
    match_lines = 0
    for raw in lines:
        stripped = _normalize_non_match_line(raw)
        parsed = parse_match_line(stripped)
        if parsed:
            match_lines += 1
            normalized_line = format_match_line(parsed)
        else:
            normalized_line = stripped
        normalized.append(normalized_line)
        if normalized_line != raw:
            changed += 1
    return normalized, changed, match_lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite a text file with matches in a normalized 'Team A - Team B X:Y' format."
        )
    )
    parser.add_argument(
        "text_file",
        type=Path,
        help="Path to the text file that should be normalized in-place.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file (default: overwrite the input file).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = _normalize_unicode(args.text_file.read_text(encoding="utf-8"))
    raw_lines = text.split("\n")
    normalized_lines, changed, match_lines = _normalize_lines(raw_lines)
    normalized_text = "\n".join(normalized_lines)
    if normalized_lines and not normalized_text.endswith("\n"):
        normalized_text += "\n"
    output_path = args.output or args.text_file
    output_path.write_text(normalized_text, encoding="utf-8")
    print(
        f"Normalized {match_lines} match lines in {args.text_file}; "
        f"{changed} line(s) updated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
