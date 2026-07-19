from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import models as m

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def global_search(q: str, limit: int = 10, db: Session = Depends(get_db)):
    players = db.query(m.Player).filter(m.Player.name.ilike(f"%{q}%")).limit(limit).all()
    teams = db.query(m.Team).filter(m.Team.name.ilike(f"%{q}%")).limit(limit).all()
    return {
        "players": [{"id": p.id, "name": p.name, "nationality": p.nationality} for p in players],
        "teams": [{"id": t.id, "name": t.name, "country": t.country} for t in teams],
    }
