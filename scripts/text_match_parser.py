#!/usr/bin/env python3
"""Helpers for parsing score lines from plain text snippets."""
from __future__ import annotations

import re
from typing import Dict, Optional

MATCH_PATTERNS = [
    # Format: Team 1 2 : 1 Team 2
    re.compile(
        r"^(?P<home>.+?)\s+(?P<home_goals>\d+)\s*[:\-]\s*(?P<away_goals>\d+)\s+(?P<away>.+)$"
    ),
    # Format: Team 1 - Team 2 2:1 (score at the end)
    re.compile(
        r"^(?P<home>.+?)\s*[-–]\s*(?P<away>.+?)\s+(?P<home_goals>\d+)\s*[:\-]\s*(?P<away_goals>\d+)$"
    ),
    # Format: Team 1 – Team 2: 3–1 (score after colon, dash between digits)
    re.compile(
        r"^(?P<home>.+?)\s*[-–]\s*(?P<away>.+?)\s*[:：]\s*(?P<home_goals>\d+)\s*[-–]\s*(?P<away_goals>\d+)$"
    ),
]


def parse_match_line(line: str) -> Optional[Dict[str, str]]:
    """Return parsed match components or None if the line is not a match."""
    stripped = line.strip()
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
