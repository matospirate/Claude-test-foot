"""Ingests real fixtures/results from the openfootball/football.json GitHub project.

Source: https://github.com/openfootball/football.json (public domain / open data,
community-maintained scores for the top European leagues). Gives real match
results and lets us compute real league standings, but has no event-level detail
(no shots/passes) - that richer layer comes from the StatsBomb ingestion instead.
"""
import datetime as dt
from collections import defaultdict

import httpx

from app.core.config import OPENFOOTBALL_RAW_BASE, DATA_DIR
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.models import models as m

CACHE_DIR = DATA_DIR / "cache" / "openfootball"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LEAGUES = {
    "en.1": "Premier League",
    "es.1": "La Liga",
    "it.1": "Serie A",
    "de.1": "Bundesliga",
    "fr.1": "Ligue 1",
}

_client = httpx.Client(timeout=30.0)


def _fetch(season: str, code: str):
    cache_file = CACHE_DIR / f"{season}_{code}.json"
    if cache_file.exists():
        import json
        return json.loads(cache_file.read_text())
    url = f"{OPENFOOTBALL_RAW_BASE}/{season}/{code}.json"
    resp = _client.get(url)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(resp.text)
    return data


def ingest_league_season(season: str, code: str):
    init_db()
    league_name = LEAGUES[code]
    data = _fetch(season, code)
    db = SessionLocal()
    try:
        db.query(m.LeagueMatch).filter_by(league_code=code, season=season).delete()

        table = defaultdict(lambda: {"played": 0, "won": 0, "drawn": 0, "lost": 0,
                                      "gf": 0, "ga": 0})

        for round_num, match in enumerate(data["matches"], start=1):
            score = match.get("score")
            match_date = None
            if match.get("date"):
                match_date = dt.datetime.strptime(match["date"], "%Y-%m-%d").date()
            matchday = None
            if match.get("round", "").lower().startswith("matchday"):
                try:
                    matchday = int(match["round"].split()[-1])
                except ValueError:
                    matchday = None

            # some rows carry score as a bare [0, 0] list, which in this feed means
            # "not yet reported" rather than a confirmed scoreless draw - treat as unknown
            home_score = away_score = None
            if isinstance(score, dict) and "ft" in score:
                home_score, away_score = score["ft"][0], score["ft"][1]

            db.add(m.LeagueMatch(
                league_code=code, league_name=league_name, season=season,
                match_date=match_date, matchday=matchday,
                home_team=match["team1"], away_team=match["team2"],
                home_score=home_score, away_score=away_score,
            ))

            if home_score is None:
                continue
            h, a = match["team1"], match["team2"]
            table[h]["played"] += 1
            table[a]["played"] += 1
            table[h]["gf"] += home_score
            table[h]["ga"] += away_score
            table[a]["gf"] += away_score
            table[a]["ga"] += home_score
            if home_score > away_score:
                table[h]["won"] += 1
                table[a]["lost"] += 1
            elif home_score < away_score:
                table[a]["won"] += 1
                table[h]["lost"] += 1
            else:
                table[h]["drawn"] += 1
                table[a]["drawn"] += 1

        db.query(m.Standing).filter_by(league_code=code, season=season).delete()
        rows = []
        for team, s in table.items():
            points = s["won"] * 3 + s["drawn"]
            rows.append((team, s, points))
        rows.sort(key=lambda r: (-r[2], -(r[1]["gf"] - r[1]["ga"]), -r[1]["gf"]))

        for pos, (team, s, points) in enumerate(rows, start=1):
            db.add(m.Standing(
                league_code=code, league_name=league_name, season=season,
                team_name=team, played=s["played"], won=s["won"], drawn=s["drawn"],
                lost=s["lost"], goals_for=s["gf"], goals_against=s["ga"],
                goal_diff=s["gf"] - s["ga"], points=points, position=pos,
            ))

        db.commit()
        print(f"{league_name} {season}: {len(data['matches'])} matches, {len(rows)} teams in table")
    finally:
        db.close()


def ingest_all(seasons=("2025-26", "2024-25")):
    for season in seasons:
        for code in LEAGUES:
            ingest_league_season(season, code)


if __name__ == "__main__":
    ingest_all()
