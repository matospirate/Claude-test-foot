from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import models as m

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.get(m.Match, match_id)
    if not match:
        raise HTTPException(404, "Match not found")

    team_stats = db.query(m.TeamMatchStat).filter_by(match_id=match_id).all()
    lineups = (
        db.query(m.LineupEntry)
        .filter_by(match_id=match_id)
        .order_by(m.LineupEntry.is_starter.desc(), m.LineupEntry.minutes_played.desc())
        .all()
    )
    goals = (
        db.query(m.Shot)
        .filter_by(match_id=match_id, outcome="Goal")
        .order_by(m.Shot.minute)
        .all()
    )

    def team_stat_dict(team_id):
        ts = next((t for t in team_stats if t.team_id == team_id), None)
        if not ts:
            return None
        return {
            "shots": ts.shots, "shots_on_target": ts.shots_on_target, "xg": round(ts.xg, 2),
            "possession_pct": round(ts.possession_pct, 1) if ts.possession_pct else None,
            "ppda": round(ts.ppda, 2) if ts.ppda else None,
            "passes_completed": ts.passes_completed, "passes_attempted": ts.passes_attempted,
            "fouls": ts.fouls,
        }

    def lineup_list(team_id):
        return [
            {
                "player_id": l.player_id, "name": l.player.name, "position": l.position,
                "jersey_number": l.jersey_number, "is_starter": l.is_starter,
                "minutes_played": l.minutes_played,
            }
            for l in lineups if l.team_id == team_id
        ]

    return {
        "id": match.id,
        "date": match.match_date,
        "stadium": match.stadium,
        "competition": {"id": match.competition.id, "name": match.competition.name,
                         "season": match.competition.season_name},
        "home_team": {"id": match.home_team.id, "name": match.home_team.name,
                      "score": match.home_score, "stats": team_stat_dict(match.home_team_id),
                      "lineup": lineup_list(match.home_team_id)},
        "away_team": {"id": match.away_team.id, "name": match.away_team.name,
                      "score": match.away_score, "stats": team_stat_dict(match.away_team_id),
                      "lineup": lineup_list(match.away_team_id)},
        "goals": [
            {"minute": g.minute, "player": g.player.name if g.player else None,
             "team_id": g.team_id, "xg": round(g.xg, 3) if g.xg else 0,
             "body_part": g.body_part, "technique": g.technique}
            for g in goals
        ],
    }


@router.get("/{match_id}/shots")
def match_shots(match_id: int, db: Session = Depends(get_db)):
    shots = db.query(m.Shot).filter_by(match_id=match_id).all()
    return [
        {
            "id": s.id, "player_id": s.player_id,
            "player_name": s.player.name if s.player else None,
            "team_id": s.team_id, "minute": s.minute, "x": s.x, "y": s.y,
            "end_x": s.end_x, "end_y": s.end_y, "body_part": s.body_part,
            "technique": s.technique, "shot_type": s.shot_type, "outcome": s.outcome,
            "xg": round(s.xg, 3) if s.xg else 0,
        }
        for s in shots
    ]


@router.get("/{match_id}/pass-network")
def match_pass_network(match_id: int, team_id: int, db: Session = Depends(get_db)):
    edges = db.query(m.PassNetworkEdge).filter_by(match_id=match_id, team_id=team_id).all()
    positions = db.query(m.PlayerAvgPosition).filter_by(match_id=match_id, team_id=team_id).all()
    return {
        "nodes": [
            {"player_id": p.player_id, "name": p.player.name, "avg_x": p.avg_x,
             "avg_y": p.avg_y, "touches": p.touch_count}
            for p in positions
        ],
        "edges": [
            {"from_player_id": e.from_player_id, "from_name": e.from_player.name,
             "to_player_id": e.to_player_id, "to_name": e.to_player.name, "count": e.count}
            for e in edges
        ],
    }


@router.get("/{match_id}/defensive-actions")
def match_defensive_actions(match_id: int, team_id: int | None = None,
                             db: Session = Depends(get_db)):
    q = db.query(m.DefensiveAction).filter_by(match_id=match_id)
    if team_id:
        q = q.filter_by(team_id=team_id)
    rows = q.all()
    return [
        {
            "player_id": r.player_id, "player_name": r.player.name if r.player else None,
            "team_id": r.team_id, "minute": r.minute, "x": r.x, "y": r.y,
            "action_type": r.action_type, "outcome": r.outcome,
        }
        for r in rows
    ]
