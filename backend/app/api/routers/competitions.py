from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.models import models as m

router = APIRouter(prefix="/api/competitions", tags=["competitions"])


@router.get("")
def list_competitions(db: Session = Depends(get_db)):
    comps = db.query(m.Competition).filter_by(source="statsbomb").all()
    out = []
    for c in comps:
        n_matches = db.query(m.Match).filter_by(competition_id=c.id, events_ingested=True).count()
        out.append({
            "id": c.id, "name": c.name, "season_name": c.season_name,
            "gender": c.gender, "country": c.country, "matches_ingested": n_matches,
        })
    return out


@router.get("/{competition_id}/matches")
def competition_matches(competition_id: int, db: Session = Depends(get_db)):
    matches = (
        db.query(m.Match)
        .filter_by(competition_id=competition_id)
        .order_by(m.Match.match_date)
        .all()
    )
    return [
        {
            "id": mt.id,
            "match_date": mt.match_date,
            "match_week": mt.match_week,
            "stadium": mt.stadium,
            "home_team": {"id": mt.home_team.id, "name": mt.home_team.name},
            "away_team": {"id": mt.away_team.id, "name": mt.away_team.name},
            "home_score": mt.home_score,
            "away_score": mt.away_score,
        }
        for mt in matches
    ]


@router.get("/{competition_id}/standings")
def competition_standings(competition_id: int, db: Session = Depends(get_db)):
    """Real standings computed from actual match results in this competition (works for
    league-format competitions; for knockout/group tournaments this reflects group play only)."""
    matches = (
        db.query(m.Match)
        .filter_by(competition_id=competition_id)
        .filter(m.Match.home_score.isnot(None))
        .all()
    )
    table = defaultdict(lambda: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0})
    for mt in matches:
        h, a = mt.home_team.name, mt.away_team.name
        table[h]["played"] += 1
        table[a]["played"] += 1
        table[h]["gf"] += mt.home_score
        table[h]["ga"] += mt.away_score
        table[a]["gf"] += mt.away_score
        table[a]["ga"] += mt.home_score
        if mt.home_score > mt.away_score:
            table[h]["won"] += 1
            table[a]["lost"] += 1
        elif mt.home_score < mt.away_score:
            table[a]["won"] += 1
            table[h]["lost"] += 1
        else:
            table[h]["drawn"] += 1
            table[a]["drawn"] += 1

    rows = []
    for team, s in table.items():
        points = s["won"] * 3 + s["drawn"]
        rows.append({**s, "team": team, "points": points, "goal_diff": s["gf"] - s["ga"]})
    rows.sort(key=lambda r: (-r["points"], -r["goal_diff"], -r["gf"]))
    for i, r in enumerate(rows, start=1):
        r["position"] = i
    return rows


@router.get("/{competition_id}/leaders")
def competition_leaders(competition_id: int, stat: str = "goals", limit: int = 20,
                         db: Session = Depends(get_db)):
    """Real per-player leaderboards (goals, assists, xg, xa, key_passes, tackles, ...)."""
    valid_stats = {c.name for c in m.PlayerMatchStat.__table__.columns
                   if c.name not in ("id", "match_id", "player_id", "team_id")}
    if stat not in valid_stats:
        raise HTTPException(400, f"Unknown stat '{stat}'. Valid: {sorted(valid_stats)}")

    col = getattr(m.PlayerMatchStat, stat)
    rows = (
        db.query(
            m.Player.id, m.Player.name, m.Team.name.label("team_name"),
            func.sum(col).label("total"),
            func.sum(m.PlayerMatchStat.minutes_played).label("minutes"),
            func.count(m.PlayerMatchStat.id).label("matches"),
        )
        .join(m.Player, m.Player.id == m.PlayerMatchStat.player_id)
        .join(m.Team, m.Team.id == m.PlayerMatchStat.team_id)
        .join(m.Match, m.Match.id == m.PlayerMatchStat.match_id)
        .filter(m.Match.competition_id == competition_id)
        .group_by(m.Player.id, m.Team.name)
        .order_by(func.sum(col).desc())
        .limit(limit)
        .all()
    )
    return [
        {"player_id": r.id, "player_name": r.name, "team_name": r.team_name,
         "value": round(r.total, 2) if r.total else 0, "minutes": r.minutes, "matches": r.matches}
        for r in rows
    ]
