import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'football.db'}")

STATSBOMB_RAW_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
OPENFOOTBALL_RAW_BASE = "https://raw.githubusercontent.com/openfootball/football.json/master"

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
