"""Ingests real match & event data from the StatsBomb open-data project into our DB.

Source: https://github.com/statsbomb/open-data (CC BY-NC-SA 4.0 - free for public/
non-commercial use with attribution). Provides genuine event-by-event data (shots
with StatsBomb's own xG model, passes, dribbles, defensive actions, pressures,
lineups with exact minutes played) for a curated set of competitions/seasons.
"""
import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.models import models as m
from app.ingestion import statsbomb_client as sb

PITCH_LENGTH = 120.0
PROGRESSIVE_THRESHOLD = 10.0  # yards of forward progress, FBref-style definition

DEFENSIVE_ACTION_TYPES = {"Duel", "Interception", "Foul Committed", "Tackle"}
TOUCH_TYPES = {
    "Pass", "Ball Receipt*", "Carry", "Shot", "Dribble", "Miscontrol",
    "Clearance", "Goal Keeper", "Duel",
}


def _get_or_create_team(db: Session, team_id: int, team_name: str, country: str = None) -> m.Team:
    team = db.query(m.Team).filter_by(statsbomb_id=team_id).first()
    if team:
        return team
    team = m.Team(statsbomb_id=team_id, name=team_name, country=country, source="statsbomb")
    db.add(team)
    db.flush()
    return team


def _get_or_create_player(db: Session, player_id: int, player_name: str, nickname: str = None) -> m.Player:
    player = db.query(m.Player).filter_by(statsbomb_id=player_id).first()
    if player:
        return player
    player = m.Player(statsbomb_id=player_id, name=player_name, known_name=nickname)
    db.add(player)
    db.flush()
    return player


def ingest_competition_season(competition_id: int, season_id: int):
    init_db()
    db = SessionLocal()
    try:
        competitions = sb.get_competitions()
        meta = next(
            c for c in competitions
            if c["competition_id"] == competition_id and c["season_id"] == season_id
        )

        competition = db.query(m.Competition).filter_by(
            statsbomb_competition_id=competition_id, statsbomb_season_id=season_id
        ).first()
        if not competition:
            competition = m.Competition(
                statsbomb_competition_id=competition_id,
                statsbomb_season_id=season_id,
                name=meta["competition_name"],
                season_name=meta["season_name"],
                gender=meta.get("competition_gender"),
                country=meta.get("country_name"),
                source="statsbomb",
            )
            db.add(competition)
            db.flush()

        matches_meta = sb.get_matches(competition_id, season_id)
        print(f"[{meta['competition_name']} {meta['season_name']}] {len(matches_meta)} matches")

        for i, mm in enumerate(matches_meta):
            match_id = mm["match_id"]
            existing = db.query(m.Match).filter_by(statsbomb_match_id=match_id).first()
            home_team = _get_or_create_team(
                db, mm["home_team"]["home_team_id"], mm["home_team"]["home_team_name"],
                mm["home_team"].get("country", {}).get("name"),
            )
            away_team = _get_or_create_team(
                db, mm["away_team"]["away_team_id"], mm["away_team"]["away_team_name"],
                mm["away_team"].get("country", {}).get("name"),
            )
            match_date = dt.datetime.strptime(mm["match_date"], "%Y-%m-%d").date()

            if not existing:
                existing = m.Match(
                    statsbomb_match_id=match_id,
                    competition_id=competition.id,
                    match_date=match_date,
                    match_week=mm.get("match_week"),
                    stadium=(mm.get("stadium") or {}).get("name"),
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_score=mm.get("home_score"),
                    away_score=mm.get("away_score"),
                )
                db.add(existing)
                db.flush()

            if not existing.events_ingested:
                try:
                    _ingest_match_events(db, existing, home_team, away_team)
                    existing.events_ingested = True
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"  ! match {match_id} failed: {e}")
            if (i + 1) % 10 == 0:
                print(f"  ...{i + 1}/{len(matches_meta)} matches processed")

        db.commit()
        print(f"Done: {meta['competition_name']} {meta['season_name']}")
    finally:
        db.close()


def _minutes_from_positions(positions, match_end_seconds):
    total_seconds = 0.0
    for p in positions:
        f = _clock_to_seconds(p["from"])
        t = _clock_to_seconds(p["to"]) if p.get("to") else match_end_seconds
        total_seconds += max(0.0, t - f)
    return round(total_seconds / 60.0)


def _clock_to_seconds(clock: str) -> float:
    parts = clock.split(":")
    mins = int(parts[0])
    secs = float(parts[1])
    return mins * 60 + secs


def _ingest_match_events(db: Session, match: m.Match, home_team: m.Team, away_team: m.Team):
    lineups = sb.get_lineups(match.statsbomb_match_id)
    team_by_sb_id = {home_team.statsbomb_id: home_team, away_team.statsbomb_id: away_team}
    player_lookup = {}  # sb player_id -> Player row

    events = sb.get_events(match.statsbomb_match_id)
    # period 5 = penalty shootout: not part of normal play, excluded from all stats
    # (shootout goals don't count toward golden boot / player stats in real football)
    events = [e for e in events if e.get("period", 1) <= 4]
    match_end_seconds = max(
        (e.get("minute", 0) * 60 + e.get("second", 0) for e in events), default=90 * 60
    )

    for team_lineup in lineups:
        team_id = team_lineup["team_id"]
        team_row = team_by_sb_id.get(team_id)
        if team_row is None:
            team_row = _get_or_create_team(db, team_id, team_lineup["team_name"])
        for p in team_lineup["lineup"]:
            player_row = _get_or_create_player(db, p["player_id"], p["player_name"], p.get("player_nickname"))
            player_lookup[p["player_id"]] = player_row

            existing_hist = db.query(m.PlayerTeamHistory).filter_by(
                player_id=player_row.id, team_id=team_row.id, competition_id=match.competition_id
            ).first()
            if not existing_hist:
                db.add(m.PlayerTeamHistory(
                    player_id=player_row.id, team_id=team_row.id, competition_id=match.competition_id
                ))

            positions = p.get("positions", [])
            minutes = _minutes_from_positions(positions, match_end_seconds) if positions else 0
            is_starter = any(pos.get("start_reason") == "Starting XI" for pos in positions)
            main_position = positions[0]["position"] if positions else None

            db.add(m.LineupEntry(
                match_id=match.id, team_id=team_row.id, player_id=player_row.id,
                jersey_number=p.get("jersey_number"), position=main_position,
                is_starter=is_starter, minutes_played=minutes,
            ))

            yellow = sum(1 for c in p.get("cards", []) if "Yellow" in c.get("card_type", ""))
            red = sum(1 for c in p.get("cards", []) if c.get("card_type") == "Red Card")
            if yellow or red:
                stat = _get_stat(db, match.id, player_row.id, team_row.id)
                stat.yellow_cards += yellow
                stat.red_cards += red
    db.flush()

    dirs = _compute_attacking_directions(events, home_team.statsbomb_id, away_team.statsbomb_id)

    events_by_id = {e["id"]: e for e in events}
    pass_edge_counts = defaultdict(int)  # (team_row_id, from_player_id, to_player_id) -> count
    avg_pos_sum = defaultdict(lambda: [0.0, 0.0, 0])  # (team_row_id, player_id) -> [sumx, sumy, n]
    team_stat_acc = defaultdict(lambda: defaultdict(float))  # team_row_id -> field -> value

    for e in events:
        etype = e["type"]["name"]
        team_sb_id = e.get("team", {}).get("id")
        team_row = team_by_sb_id.get(team_sb_id)
        player_sb = e.get("player")
        period = e.get("period", 1)
        loc = e.get("location")

        if team_row is None:
            continue

        if loc and player_sb and etype in TOUCH_TYPES:
            key = (team_row.id, player_sb["id"])
            s = avg_pos_sum[key]
            s[0] += loc[0]; s[1] += loc[1]; s[2] += 1

        player_row = player_lookup.get(player_sb["id"]) if player_sb else None
        stat = _get_stat(db, match.id, player_row.id, team_row.id) if player_row else None

        if etype == "Pass":
            pass_info = e.get("pass", {})
            completed = "outcome" not in pass_info
            if stat:
                stat.passes_attempted += 1
                if completed:
                    stat.passes_completed += 1
                if pass_info.get("cross"):
                    stat.crosses_attempted += 1
                    if completed:
                        stat.crosses_completed += 1
                if pass_info.get("through_ball"):
                    stat.through_balls += 1
                if pass_info.get("shot_assist"):
                    stat.key_passes += 1
                if pass_info.get("goal_assist"):
                    stat.assists += 1
                end_loc = pass_info.get("end_location")
                if loc and end_loc and completed:
                    if _is_progressive(team_row.statsbomb_id, period, loc[0], end_loc[0], dirs):
                        stat.progressive_passes += 1
            team_stat_acc[team_row.id]["passes_attempted"] += 1
            if completed:
                team_stat_acc[team_row.id]["passes_completed"] += 1
                recipient = pass_info.get("recipient")
                if recipient and player_sb:
                    pass_edge_counts[(team_row.id, player_sb["id"], recipient["id"])] += 1

        elif etype == "Shot":
            shot_info = e.get("shot", {})
            outcome = shot_info.get("outcome", {}).get("name")
            xg = shot_info.get("statsbomb_xg", 0.0) or 0.0
            end_loc = shot_info.get("end_location", [None, None, None])
            db.add(m.Shot(
                match_id=match.id, player_id=player_row.id if player_row else None,
                team_id=team_row.id, minute=e.get("minute"), second=e.get("second"),
                x=loc[0] if loc else None, y=loc[1] if loc else None,
                end_x=end_loc[0] if len(end_loc) > 0 else None,
                end_y=end_loc[1] if len(end_loc) > 1 else None,
                end_z=end_loc[2] if len(end_loc) > 2 else None,
                body_part=(shot_info.get("body_part") or {}).get("name"),
                technique=(shot_info.get("technique") or {}).get("name"),
                shot_type=(shot_info.get("type") or {}).get("name"),
                outcome=outcome, xg=xg,
                is_first_time=bool(shot_info.get("first_time")),
                under_pressure=bool(e.get("under_pressure")),
            ))
            if stat:
                stat.shots += 1
                stat.xg += xg
                if outcome in ("Goal", "Saved", "Saved to Post"):
                    stat.shots_on_target += 1
                if outcome == "Goal":
                    stat.goals += 1
            team_stat_acc[team_row.id]["shots"] += 1
            team_stat_acc[team_row.id]["xg"] += xg
            if outcome in ("Goal", "Saved", "Saved to Post"):
                team_stat_acc[team_row.id]["shots_on_target"] += 1
            key_pass_id = shot_info.get("key_pass_id")
            if key_pass_id and key_pass_id in events_by_id:
                passer = events_by_id[key_pass_id].get("player")
                if passer:
                    passer_row = player_lookup.get(passer["id"])
                    if passer_row:
                        pstat = _get_stat(db, match.id, passer_row.id, team_row.id)
                        pstat.xa += xg

        elif etype == "Dribble":
            outcome = (e.get("dribble") or {}).get("outcome", {}).get("name")
            if stat:
                stat.dribbles_attempted += 1
                if outcome == "Complete":
                    stat.dribbles_completed += 1

        elif etype == "Carry":
            end_loc = e.get("carry", {}).get("end_location")
            if stat:
                stat.carries += 1
                if loc and end_loc and _is_progressive(team_row.statsbomb_id, period, loc[0], end_loc[0], dirs):
                    stat.progressive_carries += 1

        elif etype in ("Interception", "Clearance", "Block", "Ball Recovery"):
            action_map = {"Interception": "Interception", "Clearance": "Clearance",
                          "Block": "Block", "Ball Recovery": "Ball Recovery"}
            db.add(m.DefensiveAction(
                match_id=match.id, player_id=player_row.id if player_row else None,
                team_id=team_row.id, minute=e.get("minute"),
                x=loc[0] if loc else None, y=loc[1] if loc else None,
                action_type=action_map[etype],
            ))
            if stat:
                if etype == "Interception":
                    stat.interceptions += 1
                elif etype == "Clearance":
                    stat.clearances += 1
                elif etype == "Block":
                    stat.blocks += 1
                elif etype == "Ball Recovery":
                    stat.ball_recoveries += 1

        elif etype == "Duel":
            duel_type = (e.get("duel", {}).get("type") or {}).get("name")
            outcome = (e.get("duel", {}).get("outcome") or {}).get("name")
            if duel_type == "Tackle" and stat:
                stat.tackles += 1
                if outcome in ("Won", "Success", "Success In Play", "Success Out"):
                    stat.tackles_won += 1
            db.add(m.DefensiveAction(
                match_id=match.id, player_id=player_row.id if player_row else None,
                team_id=team_row.id, minute=e.get("minute"),
                x=loc[0] if loc else None, y=loc[1] if loc else None,
                action_type="Tackle" if duel_type == "Tackle" else "Aerial Duel",
                outcome=outcome,
            ))

        elif etype == "Pressure":
            if stat:
                stat.pressures += 1

        elif etype == "Foul Committed":
            if stat:
                stat.fouls_committed += 1
            team_stat_acc[team_row.id]["fouls"] += 1

        elif etype == "Foul Won":
            if stat:
                stat.fouls_won += 1

        elif etype == "Dispossessed":
            if stat:
                stat.dispossessed += 1

        elif etype == "Own Goal Against":
            if stat:
                stat.own_goals += 1

    # PPDA: opponent's passes in their own defensive 60% zone / team's defensive actions in that zone
    ppda_num = defaultdict(int)  # team_row_id -> opponent passes in opp defensive zone
    ppda_den = defaultdict(int)  # team_row_id -> own defensive actions in that same zone
    for e in events:
        etype = e["type"]["name"]
        team_sb_id = e.get("team", {}).get("id")
        team_row = team_by_sb_id.get(team_sb_id)
        loc = e.get("location")
        period = e.get("period", 1)
        if team_row is None or not loc:
            continue
        opponent_row = away_team if team_row.id == home_team.id else home_team
        opp_dir = dirs.get((opponent_row.statsbomb_id, period), 1)
        # opponent's own defensive 60% zone (60% of pitch closest to opponent's own goal)
        if opp_dir == 1:
            zone = (0, 0.6 * PITCH_LENGTH)
        else:
            zone = (PITCH_LENGTH - 0.6 * PITCH_LENGTH, PITCH_LENGTH)

        if etype == "Pass" and zone[0] <= loc[0] <= zone[1]:
            ppda_num[opponent_row.id] += 1
        if etype in DEFENSIVE_ACTION_TYPES and zone[0] <= loc[0] <= zone[1]:
            ppda_den[team_row.id] += 1

    for team_row in (home_team, away_team):
        acc = team_stat_acc[team_row.id]
        total_passes = (team_stat_acc[home_team.id]["passes_attempted"]
                        + team_stat_acc[away_team.id]["passes_attempted"])
        possession = (acc["passes_attempted"] / total_passes * 100) if total_passes else None
        ppda = (ppda_num[team_row.id] / ppda_den[team_row.id]) if ppda_den[team_row.id] else None
        db.add(m.TeamMatchStat(
            match_id=match.id, team_id=team_row.id,
            shots=int(acc["shots"]), shots_on_target=int(acc["shots_on_target"]),
            xg=acc["xg"], passes_attempted=int(acc["passes_attempted"]),
            passes_completed=int(acc["passes_completed"]), possession_pct=possession,
            ppda=ppda, fouls=int(acc["fouls"]),
        ))

    for (team_row_id, from_id, to_id), count in pass_edge_counts.items():
        from_player = player_lookup.get(from_id)
        to_player = player_lookup.get(to_id)
        if from_player and to_player:
            db.add(m.PassNetworkEdge(
                match_id=match.id, team_id=team_row_id,
                from_player_id=from_player.id, to_player_id=to_player.id, count=count,
            ))

    for (team_row_id, player_sb_id), (sx, sy, n) in avg_pos_sum.items():
        player_row = player_lookup.get(player_sb_id)
        if player_row and n:
            db.add(m.PlayerAvgPosition(
                match_id=match.id, team_id=team_row_id, player_id=player_row.id,
                avg_x=sx / n, avg_y=sy / n, touch_count=n,
            ))

    db.flush()


def _get_stat(db: Session, match_id: int, player_id: int, team_id: int) -> m.PlayerMatchStat:
    stat = db.query(m.PlayerMatchStat).filter_by(match_id=match_id, player_id=player_id).first()
    if not stat:
        # minutes_played is filled in from the LineupEntry pass above; look it up
        lineup = db.query(m.LineupEntry).filter_by(match_id=match_id, player_id=player_id).first()
        stat = m.PlayerMatchStat(
            match_id=match_id, player_id=player_id, team_id=team_id,
            minutes_played=lineup.minutes_played if lineup else 0,
        )
        db.add(stat)
        db.flush()
    return stat


def _compute_attacking_directions(events, home_sb_id, away_sb_id):
    """Returns {(team_sb_id, period): +1 or -1} where +1 means the team attacks toward x=120."""
    dirs = {}
    periods = sorted(set(e.get("period", 1) for e in events))
    for period in periods:
        shot_x_by_team = defaultdict(list)
        for e in events:
            if e.get("period") != period or e["type"]["name"] != "Shot":
                continue
            loc = e.get("location")
            team_sb_id = e.get("team", {}).get("id")
            if loc and team_sb_id:
                shot_x_by_team[team_sb_id].append(loc[0])

        if shot_x_by_team:
            ref_team, xs = max(shot_x_by_team.items(), key=lambda kv: len(kv[1]))
            mean_x = sum(xs) / len(xs)
            ref_dir = 1 if mean_x > 60 else -1
        else:
            # fallback: assume standard alternating convention
            ref_team = home_sb_id
            ref_dir = 1 if period % 2 == 1 else -1

        other_team = away_sb_id if ref_team == home_sb_id else home_sb_id
        dirs[(ref_team, period)] = ref_dir
        dirs[(other_team, period)] = -ref_dir

    return dirs


def _is_progressive(team_row_id, period, start_x, end_x, dirs):
    d = dirs.get((team_row_id, period))
    if d is None:
        return False
    return (end_x - start_x) * d >= PROGRESSIVE_THRESHOLD


if __name__ == "__main__":
    import sys
    comp_id, season_id = int(sys.argv[1]), int(sys.argv[2])
    ingest_competition_season(comp_id, season_id)
