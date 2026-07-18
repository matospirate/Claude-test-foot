from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import models as m
from app.ingestion.openfootball_ingest import LEAGUES

router = APIRouter(prefix="/api/leagues", tags=["leagues"])


@router.get("")
def list_leagues(db: Session = Depends(get_db)):
    seasons = [s for (s,) in db.query(distinct(m.Standing.season)).all()]
    return [
        {"code": code, "name": name, "seasons": sorted(seasons, reverse=True)}
        for code, name in LEAGUES.items()
    ]


@router.get("/{code}/standings")
def get_standings(code: str, season: str = "2025-26", db: Session = Depends(get_db)):
    rows = (
        db.query(m.Standing)
        .filter_by(league_code=code, season=season)
        .order_by(m.Standing.position)
        .all()
    )
    if not rows:
        raise HTTPException(404, "No standings found for this league/season")
    return rows


@router.get("/{code}/matches")
def get_league_matches(code: str, season: str = "2025-26", matchday: int | None = None,
                        db: Session = Depends(get_db)):
    q = db.query(m.LeagueMatch).filter_by(league_code=code, season=season)
    if matchday:
        q = q.filter_by(matchday=matchday)
    return q.order_by(m.LeagueMatch.match_date).all()


@router.get("/{code}/top-scorers")
def top_scorers_placeholder(code: str, season: str = "2025-26"):
    # openfootball only carries score-level results (no per-player goal data);
    # per-player leaderboards are only available for StatsBomb-covered
    # competitions - see /api/competitions instead.
    return {
        "detail": (
            "Top scorer data requires event-level stats, only available for "
            "StatsBomb-covered competitions. See GET /api/competitions."
        )
    }
