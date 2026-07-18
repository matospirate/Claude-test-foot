from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.db.init_db import init_db
from app.api.routers import leagues, competitions, players, teams, matches, compare, search

init_db()

app = FastAPI(
    title="Football Analytics API",
    description=(
        "Real football data: standings/results from openfootball, and deep "
        "event-level stats (xG, passes, defensive actions) from StatsBomb open-data."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leagues.router)
app.include_router(competitions.router)
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(compare.router)
app.include_router(search.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
