from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import models as m

router = APIRouter(prefix="/api/players", tags=["players"])

AGG_FIELDS = [c.name for c in m.PlayerMatchStat.__table__.columns
              if c.name not in ("id", "match_id", "player_id", "team_id")]


def _aggregate_stats(db: Session, query):
    rows = query.all()
    totals = {f: 0 for f in AGG_FIELDS}
    n_matches = 0
    for row in rows:
        n_matches += 1
        for f in AGG_FIELDS:
            totals[f] += getattr(row, f) or 0
    return totals, n_matches


@router.get("/search")
def search_players(q: str, limit: int = 20, db: Session = Depends(get_db)):
    players = (
        db.query(m.Player)
        .filter(m.Player.name.ilike(f"%{q}%"))
        .limit(limit)
        .all()
    )
    return [{"id": p.id, "name": p.name, "nationality": p.nationality} for p in players]


@router.get("/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.get(m.Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")

    teams = (
        db.query(m.Team, m.Competition)
        .join(m.PlayerTeamHistory, m.PlayerTeamHistory.team_id == m.Team.id)
        .join(m.Competition, m.Competition.id == m.PlayerTeamHistory.competition_id)
        .filter(m.PlayerTeamHistory.player_id == player_id)
        .all()
    )

    query = db.query(m.PlayerMatchStat).filter_by(player_id=player_id)
    totals, n_matches = _aggregate_stats(db, query)
    minutes = totals["minutes_played"] or 1
    per90 = {f: round(v / minutes * 90, 3) for f, v in totals.items()
              if f not in ("minutes_played",)}

    return {
        "id": player.id,
        "name": player.name,
        "known_name": player.known_name,
        "nationality": player.nationality,
        "primary_position": player.primary_position,
        "teams_competitions": [
            {"team": t.name, "competition": c.name, "season": c.season_name}
            for t, c in teams
        ],
        "career_totals": {"matches": n_matches, **totals},
        "per_90": per90,
    }


@router.get("/{player_id}/matches")
def player_matches(player_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(m.PlayerMatchStat, m.Match)
        .join(m.Match, m.Match.id == m.PlayerMatchStat.match_id)
        .filter(m.PlayerMatchStat.player_id == player_id)
        .order_by(m.Match.match_date)
        .all()
    )
    out = []
    for stat, match in rows:
        opponent = match.away_team.name if stat.team_id == match.home_team_id else match.home_team.name
        out.append({
            "match_id": match.id,
            "date": match.match_date,
            "competition": match.competition.name,
            "opponent": opponent,
            "score": f"{match.home_score}-{match.away_score}",
            "minutes_played": stat.minutes_played,
            "goals": stat.goals,
            "assists": stat.assists,
            "xg": round(stat.xg, 2),
            "xa": round(stat.xa, 2),
            "shots": stat.shots,
            "passes_completed": stat.passes_completed,
            "passes_attempted": stat.passes_attempted,
        })
    return out


@router.get("/{player_id}/shots")
def player_shots(player_id: int, db: Session = Depends(get_db)):
    shots = db.query(m.Shot).filter_by(player_id=player_id).all()
    return [
        {
            "match_id": s.match_id, "minute": s.minute, "x": s.x, "y": s.y,
            "end_x": s.end_x, "end_y": s.end_y, "body_part": s.body_part,
            "technique": s.technique, "shot_type": s.shot_type,
            "outcome": s.outcome, "xg": round(s.xg, 3) if s.xg else 0,
        }
        for s in shots
    ]


@router.get("/{player_id}/avg-positions")
def player_avg_positions(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(m.PlayerAvgPosition).filter_by(player_id=player_id).all()
    return [
        {"match_id": r.match_id, "avg_x": r.avg_x, "avg_y": r.avg_y, "touch_count": r.touch_count}
        for r in rows
    ]
