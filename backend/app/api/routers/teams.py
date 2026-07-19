from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.models import models as m

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("/search")
def search_teams(q: str, limit: int = 20, db: Session = Depends(get_db)):
    teams = db.query(m.Team).filter(m.Team.name.ilike(f"%{q}%")).limit(limit).all()
    return [{"id": t.id, "name": t.name, "country": t.country} for t in teams]


@router.get("/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(m.Team, team_id)
    if not team:
        raise HTTPException(404, "Team not found")

    squad_rows = (
        db.query(m.Player, func.sum(m.LineupEntry.minutes_played).label("minutes"),
                  func.count(m.LineupEntry.id).label("appearances"))
        .join(m.LineupEntry, m.LineupEntry.player_id == m.Player.id)
        .filter(m.LineupEntry.team_id == team_id)
        .group_by(m.Player.id)
        .order_by(func.sum(m.LineupEntry.minutes_played).desc())
        .all()
    )

    matches = (
        db.query(m.Match)
        .filter((m.Match.home_team_id == team_id) | (m.Match.away_team_id == team_id))
        .order_by(m.Match.match_date)
        .all()
    )

    return {
        "id": team.id,
        "name": team.name,
        "country": team.country,
        "squad": [
            {"player_id": p.id, "name": p.name, "appearances": app, "minutes": mins or 0}
            for p, mins, app in squad_rows
        ],
        "matches": [
            {
                "match_id": mt.id, "date": mt.match_date, "competition": mt.competition.name,
                "home_team": mt.home_team.name, "away_team": mt.away_team.name,
                "home_score": mt.home_score, "away_score": mt.away_score,
            }
            for mt in matches
        ],
    }


@router.get("/{team_id}/match-stats")
def team_match_stats(team_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(m.TeamMatchStat, m.Match)
        .join(m.Match, m.Match.id == m.TeamMatchStat.match_id)
        .filter(m.TeamMatchStat.team_id == team_id)
        .order_by(m.Match.match_date)
        .all()
    )
    return [
        {
            "match_id": match.id, "date": match.match_date,
            "shots": ts.shots, "shots_on_target": ts.shots_on_target, "xg": round(ts.xg, 2),
            "possession_pct": round(ts.possession_pct, 1) if ts.possession_pct else None,
            "ppda": round(ts.ppda, 2) if ts.ppda else None,
            "passes_completed": ts.passes_completed, "passes_attempted": ts.passes_attempted,
        }
        for ts, match in rows
    ]
