#!/usr/bin/env python3
"""Helpers for parsing score lines from plain text snippets."""
from __future__ import annotations

import re
from typing import Dict, Optional

INVISIBLE_CHARACTERS = "\ufeff\u200b\u200c\u200d\u2060"
_REMOVE_INVISIBLE = str.maketrans("", "", INVISIBLE_CHARACTERS)

MATCH_PATTERNS = [
    # Format: Team 1 2 : 1 Team 2 (space before the score is optional)
    re.compile(
        r"^(?P<home>.+?)\s*(?P<home_goals>\d+)\s*[:\-–]\s*(?P<away_goals>\d+)\s*(?P<away>.+)$"
    ),
    # Format: Team 1 - Team 2 2:1 (score at the end)
    re.compile(
        r"^(?P<home>.+?)\s*[-–]\s*(?P<away>.+?)\s+(?P<home_goals>\d+)\s*[:\-–]\s*(?P<away_goals>\d+)$"
    ),
    # Format: Team 1 - Team 2 2:1 (score at the end, no space before the score)
    re.compile(
        r"^(?P<home>.+?)\s*[-–]\s*(?P<away>.+?)(?P<home_goals>\d+)\s*[:\-–]\s*(?P<away_goals>\d+)$"
    ),
    # Format: Team 1 – Team 2: 3–1 (score after colon, dash between digits)
    re.compile(
        r"^(?P<home>.+?)\s*[-–]\s*(?P<away>.+?)\s*[:：]\s*(?P<home_goals>\d+)\s*[-–]\s*(?P<away_goals>\d+)$"
    ),
]

def _cleanup_line(line: str) -> str:
    """Normalize spacing and drop invisible characters for robust parsing."""
    normalized = line.replace("\xa0", " ").translate(_REMOVE_INVISIBLE)
    normalized = " ".join(normalized.strip().split())
    return normalized


def parse_match_line(line: str) -> Optional[Dict[str, str]]:
    """Return parsed match components or None if the line is not a match."""
    stripped = _cleanup_line(line)
    if not stripped or stripped.startswith("#"):
        return None
    for pattern in MATCH_PATTERNS:
        match = pattern.match(stripped)
        if match:
            return {
                "home_team": match.group("home").strip(),
                "away_team": match.group("away").strip(),
                "home_goals": match.group("home_goals"),
                "away_goals": match.group("away_goals"),
            }
    return None


def format_match_line(match: Dict[str, str]) -> str:
    """Return a normalized textual representation for a parsed match."""
    home = match["home_team"].strip()
    away = match["away_team"].strip()
    home_goals = str(match["home_goals"]).strip()
    away_goals = str(match["away_goals"]).strip()
    return f"{home} - {away} {home_goals}:{away_goals}"
