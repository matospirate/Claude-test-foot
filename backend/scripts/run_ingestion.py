"""Run the full data ingestion: StatsBomb deep-event competitions + openfootball standings.

Usage: python scripts/run_ingestion.py
"""
from app.ingestion.statsbomb_ingest import ingest_competition_season
from app.ingestion.openfootball_ingest import ingest_all as ingest_openfootball_all

# (competition_id, season_id, label) - see statsbomb open-data competitions.json for more options
STATSBOMB_TARGETS = [
    (43, 106, "FIFA World Cup 2022"),
    (55, 282, "UEFA Euro 2024"),
]

if __name__ == "__main__":
    print("=== openfootball: standings & results (top-5 leagues) ===")
    ingest_openfootball_all()

    print("\n=== StatsBomb: deep event data ===")
    for comp_id, season_id, label in STATSBOMB_TARGETS:
        print(f"\n--- {label} ---")
        ingest_competition_season(comp_id, season_id)

    print("\nAll ingestion complete.")
