"""Trims the raw export from backend/scripts/export_static_data.py down to a size
that's reasonable to embed in a single self-contained HTML file: caps the player
list to the most-used players and drops unused (0-minute) bench entries.

Usage: python trim_data.py <input.json> <output.json>
"""
import json
import sys

TOP_N_PLAYERS = 400


def trim(data):
    players = data["players"]
    players.sort(key=lambda p: p["totals"].get("minutes_played", 0), reverse=True)
    kept_players = players[:TOP_N_PLAYERS]
    kept_ids = {p["id"] for p in kept_players}
    data["players"] = kept_players

    for m in data["matches"]:
        for side in ("home", "away"):
            m[side]["lineup"] = [l for l in m[side]["lineup"] if l["min"] and l["min"] > 0]

    data["player_match_stats"] = [
        pms for pms in data["player_match_stats"] if pms["pid"] in kept_ids
    ]
    return data


if __name__ == "__main__":
    in_path, out_path = sys.argv[1], sys.argv[2]
    data = trim(json.load(open(in_path, encoding="utf-8")))
    json.dump(data, open(out_path, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"players kept: {len(data['players'])}")
    print(f"player_match_stats kept: {len(data['player_match_stats'])}")
