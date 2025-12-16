"""Utilities for normalizing team names written in multiple languages."""
from __future__ import annotations

import unicodedata

INVISIBLE_CHARACTERS = "\ufeff\u200b\u200c\u200d\u2060"
_REMOVE_INVISIBLE = str.maketrans("", "", INVISIBLE_CHARACTERS)

TEAM_ALIASES = {
    # Arsenal
    "arsenal": "arsenal",
    "арсенал": "arsenal",
    # Aston Villa
    "aston villa": "aston villa",
    "астон вилла": "aston villa",
    "астон вілла": "aston villa",
    # Bournemouth
    "bournemouth": "bournemouth",
    "борнмут": "bournemouth",
    "бортмут": "bournemouth",
    # Brentford
    "brentford": "brentford",
    "брентфорд": "brentford",
    # Brighton
    "brighton": "brighton",
    "brighton & hove albion": "brighton",
    "брайтон": "brighton",
    "брайтон энд хоув альбион": "brighton",
    "брайтон енд хоу": "brighton",
    "брайтон енд хов альбіон": "brighton",
    # Burnley
    "burnley": "burnley",
    "бернли": "burnley",
    "бернлі": "burnley",
    # Chelsea
    "chelsea": "chelsea",
    "челси": "chelsea",
    "челсі": "chelsea",
    # Crystal Palace
    "crystal palace": "crystal palace",
    "кристал пэлас": "crystal palace",
    "кристал пелес": "crystal palace",
    "крістал пелес": "crystal palace",
    # Everton
    "everton": "everton",
    "эвертон": "everton",
    "евертона": "everton",
    # Fulham
    "fulham": "fulham",
    "фулхэм": "fulham",
    "фулхем": "fulham",
    "фулгем": "fulham",
    # Ipswich Town
    "ipswich": "ipswich town",
    "ipswich town": "ipswich town",
    "ипсвич": "ipswich town",
    "іпсвіч": "ipswich town",
    # Leeds United (occasionally used in files)
    "leeds": "leeds",
    "лідс": "leeds",
    "лидс": "leeds",
    # Leicester City
    "leicester": "leicester",
    "leicester city": "leicester",
    "лейстер": "leicester",
    "лестер": "leicester",
    "лейчестер": "leicester",
    # Liverpool
    "liverpool": "liverpool",
    "ливерпуль": "liverpool",
    "ліверпуль": "liverpool",
    # Luton Town
    "luton": "luton town",
    "luton town": "luton town",
    "лутон": "luton town",
    "лутон таун": "luton town",
    # Manchester City
    "man city": "manchester city",
    "manchester city": "manchester city",
    "манчестер сити": "manchester city",
    "манчестер сіті": "manchester city",
    "мс": "manchester city",
    # Manchester United
    "man united": "manchester united",
    "manchester united": "manchester united",
    "манчестер юнайтед": "manchester united",
    "манчестер юнiтет": "manchester united",
    "манчестер юнайтед": "manchester united",
    "мю": "manchester united",
    # Newcastle United
    "newcastle": "newcastle united",
    "newcastle united": "newcastle united",
    "ньюкасл": "newcastle united",
    "ньюкасл юнайтед": "newcastle united",
    "ньюкасл юнiтет": "newcastle united",
    # Nottingham Forest
    "nottingham forest": "nottingham forest",
    "nottingham": "nottingham forest",
    "ноттингем": "nottingham forest",
    "нотоингем": "nottingham forest",
    "ноттінгем": "nottingham forest",
    "ноттінгем форест": "nottingham forest",
    # Southampton
    "southampton": "southampton",
    "саутгемптон": "southampton",
    "саутгемтон": "southampton",
    "саутгемптон": "southampton",
    # Tottenham Hotspur
    "tottenham": "tottenham hotspur",
    "tottenham hotspur": "tottenham hotspur",
    "тоттенхэм": "tottenham hotspur",
    "тоттенгем": "tottenham hotspur",
    "тоттенхем": "tottenham hotspur",
    # West Ham United
    "west ham": "west ham united",
    "west ham united": "west ham united",
    "вест хэм": "west ham united",
    "вест хем": "west ham united",
    # Wolverhampton Wanderers
    "wolverhampton": "wolverhampton wanderers",
    "wolverhampton wanderers": "wolverhampton wanderers",
    "вулверхэмптон": "wolverhampton wanderers",
    "вулверхемптон": "wolverhampton wanderers",
    # Brighton (already normalized)
    "brighton hove": "brighton",
    "brighton hove albion": "brighton",
}


def normalize_team_name(name: str) -> str:
    """Return a canonical lowercase team name for cross-language matching."""
    if not name:
        return ""
    base = unicodedata.normalize("NFKC", name)
    base = base.translate(_REMOVE_INVISIBLE).replace("\xa0", " ")
    base = base.replace("ё", "е")
    base = " ".join(base.lower().replace("-", " ").split())
    return TEAM_ALIASES.get(base, base)
