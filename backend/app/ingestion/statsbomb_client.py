"""Thin HTTP client for the StatsBomb open-data GitHub repo, with local disk caching."""
import json
from pathlib import Path

import httpx

from app.core.config import STATSBOMB_RAW_BASE, DATA_DIR

CACHE_DIR = DATA_DIR / "cache" / "statsbomb"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_client = httpx.Client(timeout=30.0)


def _cache_path(relative_path: str) -> Path:
    return CACHE_DIR / relative_path


def fetch_json(relative_path: str):
    """relative_path e.g. 'competitions.json' or 'events/3857276.json'"""
    cache_file = _cache_path(relative_path)
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    url = f"{STATSBOMB_RAW_BASE}/{relative_path}"
    resp = _client.get(url)
    resp.raise_for_status()
    data = resp.json()

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data))
    return data


def get_competitions():
    return fetch_json("competitions.json")


def get_matches(competition_id: int, season_id: int):
    return fetch_json(f"matches/{competition_id}/{season_id}.json")


def get_lineups(match_id: int):
    return fetch_json(f"lineups/{match_id}.json")


def get_events(match_id: int):
    return fetch_json(f"events/{match_id}.json")
