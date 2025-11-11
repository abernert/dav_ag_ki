"""Utilities to load host data pools (converted from wsim/)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import random
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parents[1]
WSIM_DIR = BASE_DIR.parent / "wsim"
DATA_DIR = BASE_DIR / "data"

# Fallback lists if wsim assets not available
FALLBACK_POSTCODES = [
    "W1A4WW",
    "SO211UP",
    "SO212JN",
    "TR68BK",
    "IP221PL",
    "ST106RY",
]

FALLBACK_FIRST_NAMES = ["ANDREW", "GRAHAM", "BRIAN", "TROY", "JOHNNY", "SUSAN"]
FALLBACK_SURNAMES = ["PETERS", "CUTHBERT", "CANT", "TEMPEST", "MORRIS", "STRANKS"]


def _candidate_paths(filename: str) -> Iterable[Path]:
    yield WSIM_DIR / filename
    yield DATA_DIR / filename


def _load_file(filename: str) -> list[str]:
    for path in _candidate_paths(filename):
        if path.exists():
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                return [line.strip() for line in fh if line.strip() and not line.startswith("*")]
    return []


@lru_cache(maxsize=1)
def postcodes() -> list[str]:
    data = _load_file("pcode.txt")
    if not data:
        return FALLBACK_POSTCODES
    # entries may be comma-separated (like WSIM msg tables)
    cleaned: list[str] = []
    for entry in data:
        if "(" in entry and ")" in entry:
            entry = entry.replace("(", "").replace(")", "")
        for token in entry.split(","):
            token = token.strip()
            if token:
                cleaned.append(token)
    return cleaned or FALLBACK_POSTCODES


@lru_cache(maxsize=1)
def first_names() -> list[str]:
    data = _load_file("fname.txt")
    return data or FALLBACK_FIRST_NAMES


@lru_cache(maxsize=1)
def surnames() -> list[str]:
    data = _load_file("sname.txt")
    return data or FALLBACK_SURNAMES


def random_postcode(rng: random.Random | None = None) -> str:
    rng = rng or random
    return rng.choice(postcodes())


def random_first_name(rng: random.Random | None = None) -> str:
    rng = rng or random
    return rng.choice(first_names())


def random_surname(rng: random.Random | None = None) -> str:
    rng = rng or random
    return rng.choice(surnames())
