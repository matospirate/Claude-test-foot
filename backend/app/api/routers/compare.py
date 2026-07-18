from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import models as m

router = APIRouter(prefix="/api/compare", tags=["compare"])

# A curated set of per-90 metrics that make a sensible radar profile
RADAR_METRICS = [
    "goals", "assists", "xg", "xa", "shots", "key_passes",
    "passes_completed", "progressive_passes", "progressive_carries",
    "dribbles_completed", "tackles", "interceptions", "pressures", "ball_recoveries",
]


@router.get("")
def compare_players(player_ids: str, db: Session = Depends(get_db)):
    """player_ids: comma-separated list, e.g. '12,45'"""
    ids = [int(x) for x in player_ids.split(",") if x.strip()]
    if not ids or len(ids) > 6:
        raise HTTPException(400, "Provide between 1 and 6 player_ids")

    out = []
    for pid in ids:
        player = db.get(m.Player, pid)
        if not player:
            continue
        stats = db.query(m.PlayerMatchStat).filter_by(player_id=pid).all()
        minutes = sum(s.minutes_played for s in stats) or 1
        per90 = {}
        for field in RADAR_METRICS:
            total = sum(getattr(s, field) or 0 for s in stats)
            per90[field] = round(total / minutes * 90, 3)
        out.append({
            "player_id": pid, "name": player.name,
            "minutes_played": minutes, "matches": len(stats),
            "per_90": per90,
        })
    return {"metrics": RADAR_METRICS, "players": out}
