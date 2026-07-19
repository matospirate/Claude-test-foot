"""Exports a compact JSON snapshot of the DB for a standalone (backend-less) demo artifact."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models import models as m

db = SessionLocal()

def r(x, n=3):
    return round(x, n) if isinstance(x, float) else x

# --- standings (all 5 leagues, latest season) ---
standings = {}
for code in ["en.1", "es.1", "it.1", "de.1", "fr.1"]:
    rows = db.query(m.Standing).filter_by(league_code=code, season="2025-26").order_by(m.Standing.position).all()
    if rows:
        standings[code] = {
            "league_name": rows[0].league_name,
            "season": "2025-26",
            "rows": [
                {"pos": s.position, "team": s.team_name, "p": s.played, "w": s.won, "d": s.drawn,
                 "l": s.lost, "gf": s.goals_for, "ga": s.goals_against, "gd": s.goal_diff, "pts": s.points}
                for s in rows
            ],
        }

# --- competitions ---
competitions = []
for c in db.query(m.Competition).filter_by(source="statsbomb").all():
    competitions.append({"id": c.id, "name": c.name, "season": c.season_name})

# --- players (all, with career totals across statsbomb comps) ---
AGG_FIELDS = [c.name for c in m.PlayerMatchStat.__table__.columns
              if c.name not in ("id", "match_id", "player_id", "team_id")]

players = []
all_players = db.query(m.Player).filter(m.Player.statsbomb_id.isnot(None)).all()
for p in all_players:
    stats = db.query(m.PlayerMatchStat).filter_by(player_id=p.id).all()
    if not stats:
        continue
    totals = {f: 0 for f in AGG_FIELDS}
    for s in stats:
        for f in AGG_FIELDS:
            totals[f] += getattr(s, f) or 0
    minutes = totals["minutes_played"] or 1
    teams_comps = (
        db.query(m.Team.name, m.Competition.name, m.Competition.season_name)
        .join(m.PlayerTeamHistory, m.PlayerTeamHistory.team_id == m.Team.id)
        .join(m.Competition, m.Competition.id == m.PlayerTeamHistory.competition_id)
        .filter(m.PlayerTeamHistory.player_id == p.id)
        .all()
    )
    players.append({
        "id": p.id,
        "name": p.known_name or p.name,
        "full_name": p.name,
        "teams": [{"team": t, "competition": c, "season": s} for t, c, s in teams_comps],
        "matches": len(stats),
        "totals": {k: r(v) for k, v in totals.items()},
        "per90": {k: r(v / minutes * 90) for k, v in totals.items() if k != "minutes_played"},
    })

print(f"players: {len(players)}", file=sys.stderr)

# --- matches (all statsbomb matches, with team stats + lineups + goals) ---
matches = []
for mt in db.query(m.Match).filter_by(events_ingested=True).all():
    team_stats = {ts.team_id: ts for ts in db.query(m.TeamMatchStat).filter_by(match_id=mt.id).all()}
    lineups = db.query(m.LineupEntry).filter_by(match_id=mt.id).order_by(
        m.LineupEntry.is_starter.desc(), m.LineupEntry.minutes_played.desc()
    ).all()
    goals = db.query(m.Shot).filter_by(match_id=mt.id, outcome="Goal").order_by(m.Shot.minute).all()

    def side(team_id, team_name):
        ts = team_stats.get(team_id)
        return {
            "id": team_id, "name": team_name,
            "stats": None if not ts else {
                "shots": ts.shots, "sot": ts.shots_on_target, "xg": r(ts.xg),
                "poss": r(ts.possession_pct, 1) if ts.possession_pct else None,
                "ppda": r(ts.ppda, 2) if ts.ppda else None,
                "passes_c": ts.passes_completed, "passes_a": ts.passes_attempted, "fouls": ts.fouls,
            },
            "lineup": [
                {"pid": l.player_id, "name": l.player.name, "pos": l.position, "num": l.jersey_number,
                 "starter": l.is_starter, "min": l.minutes_played}
                for l in lineups if l.team_id == team_id
            ],
        }

    matches.append({
        "id": mt.id,
        "date": str(mt.match_date),
        "stadium": mt.stadium,
        "competition_id": mt.competition_id,
        "home": {**side(mt.home_team_id, mt.home_team.name), "score": mt.home_score},
        "away": {**side(mt.away_team_id, mt.away_team.name), "score": mt.away_score},
        "goals": [
            {"min": g.minute, "player": g.player.name if g.player else None, "team_id": g.team_id, "xg": r(g.xg, 3)}
            for g in goals
        ],
    })
print(f"matches: {len(matches)}", file=sys.stderr)

# --- shots (all, for shot maps) ---
shots = []
for s in db.query(m.Shot).all():
    if s.x is None:
        continue
    shots.append({
        "match_id": s.match_id, "pid": s.player_id, "player": s.player.name if s.player else None,
        "team_id": s.team_id, "min": s.minute, "x": r(s.x, 1), "y": r(s.y, 1),
        "body": s.body_part, "type": s.shot_type, "outcome": s.outcome, "xg": r(s.xg, 3),
    })
print(f"shots: {len(shots)}", file=sys.stderr)

# --- per-match player stat lines (for the player match-log table) ---
player_match_stats = []
for s in db.query(m.PlayerMatchStat).all():
    player_match_stats.append({
        "match_id": s.match_id, "pid": s.player_id, "team_id": s.team_id,
        "min": s.minutes_played, "g": s.goals, "a": s.assists,
        "xg": r(s.xg), "xa": r(s.xa), "shots": s.shots,
        "kp": s.key_passes, "pc": s.passes_completed, "pa": s.passes_attempted,
    })
print(f"player_match_stats: {len(player_match_stats)}", file=sys.stderr)

data = {
    "standings": standings,
    "competitions": competitions,
    "players": players,
    "matches": matches,
    "shots": shots,
    "player_match_stats": player_match_stats,
}

out_path = sys.argv[1] if len(sys.argv) > 1 else "static_data.json"
with open(out_path, "w") as f:
    json.dump(data, f, separators=(",", ":"))
print(f"wrote {out_path}", file=sys.stderr)
