from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class DataSource(str):
    STATSBOMB = "statsbomb"
    OPENFOOTBALL = "openfootball"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    statsbomb_id = Column(Integer, unique=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    country = Column(String, nullable=True)
    source = Column(String, default="statsbomb")

    players = relationship("PlayerTeamHistory", back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    statsbomb_id = Column(Integer, unique=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    known_name = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    primary_position = Column(String, nullable=True)
    jersey_number = Column(Integer, nullable=True)


class PlayerTeamHistory(Base):
    """Links a player to a team within a given competition/season (as observed in lineups)."""
    __tablename__ = "player_team_history"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), index=True)

    player = relationship("Player")
    team = relationship("Team", back_populates="players")
    competition = relationship("Competition")

    __table_args__ = (UniqueConstraint("player_id", "team_id", "competition_id"),)


class Competition(Base):
    """A specific competition+season, e.g. 'FIFA World Cup 2022' or 'Ligue 1 2022/2023'."""
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True)
    statsbomb_competition_id = Column(Integer, nullable=True)
    statsbomb_season_id = Column(Integer, nullable=True)
    name = Column(String, index=True, nullable=False)
    season_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    country = Column(String, nullable=True)
    source = Column(String, default="statsbomb")

    __table_args__ = (
        UniqueConstraint("statsbomb_competition_id", "statsbomb_season_id"),
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    statsbomb_match_id = Column(Integer, unique=True, nullable=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), index=True)
    match_date = Column(Date, nullable=True)
    match_week = Column(Integer, nullable=True)
    stadium = Column(String, nullable=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    events_ingested = Column(Boolean, default=False)

    competition = relationship("Competition")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])


class LineupEntry(Base):
    __tablename__ = "lineup_entries"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    jersey_number = Column(Integer, nullable=True)
    position = Column(String, nullable=True)
    is_starter = Column(Boolean, default=False)
    minutes_played = Column(Integer, default=0)

    match = relationship("Match")
    team = relationship("Team")
    player = relationship("Player")


class Shot(Base):
    __tablename__ = "shots"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    minute = Column(Integer)
    second = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    end_x = Column(Float, nullable=True)
    end_y = Column(Float, nullable=True)
    end_z = Column(Float, nullable=True)
    body_part = Column(String, nullable=True)
    technique = Column(String, nullable=True)
    shot_type = Column(String, nullable=True)  # Open Play, Free Kick, Penalty, Corner
    outcome = Column(String, nullable=True)  # Goal, Saved, Off T, Blocked, Post, Wayward
    xg = Column(Float, nullable=True)
    is_first_time = Column(Boolean, default=False)
    under_pressure = Column(Boolean, default=False)
    key_pass_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)

    match = relationship("Match")
    player = relationship("Player", foreign_keys=[player_id])
    team = relationship("Team")


class DefensiveAction(Base):
    __tablename__ = "defensive_actions"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    minute = Column(Integer)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    action_type = Column(String)  # Tackle, Interception, Clearance, Block, Pressure, Ball Recovery
    outcome = Column(String, nullable=True)

    match = relationship("Match")
    player = relationship("Player")
    team = relationship("Team")


class PassNetworkEdge(Base):
    """Aggregated pass-combination counts between two players in a match (for pass-network viz)."""
    __tablename__ = "pass_network_edges"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    from_player_id = Column(Integer, ForeignKey("players.id"))
    to_player_id = Column(Integer, ForeignKey("players.id"))
    count = Column(Integer, default=0)

    from_player = relationship("Player", foreign_keys=[from_player_id])
    to_player = relationship("Player", foreign_keys=[to_player_id])


class PlayerAvgPosition(Base):
    """Average x,y position of a player in a match, for average-position maps."""
    __tablename__ = "player_avg_positions"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    avg_x = Column(Float)
    avg_y = Column(Float)
    touch_count = Column(Integer)

    player = relationship("Player")
    team = relationship("Team")


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)

    minutes_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    own_goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    xg = Column(Float, default=0.0)
    xa = Column(Float, default=0.0)
    key_passes = Column(Integer, default=0)
    passes_attempted = Column(Integer, default=0)
    passes_completed = Column(Integer, default=0)
    progressive_passes = Column(Integer, default=0)
    through_balls = Column(Integer, default=0)
    crosses_attempted = Column(Integer, default=0)
    crosses_completed = Column(Integer, default=0)
    touches = Column(Integer, default=0)
    dribbles_attempted = Column(Integer, default=0)
    dribbles_completed = Column(Integer, default=0)
    carries = Column(Integer, default=0)
    progressive_carries = Column(Integer, default=0)
    dispossessed = Column(Integer, default=0)
    tackles = Column(Integer, default=0)
    tackles_won = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    clearances = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    pressures = Column(Integer, default=0)
    fouls_committed = Column(Integer, default=0)
    fouls_won = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    ball_recoveries = Column(Integer, default=0)

    match = relationship("Match")
    player = relationship("Player")
    team = relationship("Team")

    __table_args__ = (UniqueConstraint("match_id", "player_id"),)


class TeamMatchStat(Base):
    __tablename__ = "team_match_stats"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)

    shots = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    xg = Column(Float, default=0.0)
    passes_attempted = Column(Integer, default=0)
    passes_completed = Column(Integer, default=0)
    possession_pct = Column(Float, nullable=True)
    ppda = Column(Float, nullable=True)
    corners = Column(Integer, default=0)
    fouls = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)

    match = relationship("Match")
    team = relationship("Team")

    __table_args__ = (UniqueConstraint("match_id", "team_id"),)


class Standing(Base):
    """League table row, sourced from openfootball results (score-level real data)."""
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True)
    league_code = Column(String, index=True)  # e.g. "en.1", "fr.1"
    league_name = Column(String)
    season = Column(String, index=True)  # e.g. "2023-24"
    team_name = Column(String, index=True)
    played = Column(Integer, default=0)
    won = Column(Integer, default=0)
    drawn = Column(Integer, default=0)
    lost = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_diff = Column(Integer, default=0)
    points = Column(Integer, default=0)
    position = Column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint("league_code", "season", "team_name"),)


class LeagueMatch(Base):
    """Lightweight result row sourced from openfootball (no deep events)."""
    __tablename__ = "league_matches"

    id = Column(Integer, primary_key=True)
    league_code = Column(String, index=True)
    league_name = Column(String)
    season = Column(String, index=True)
    match_date = Column(Date, nullable=True)
    matchday = Column(Integer, nullable=True)
    home_team = Column(String)
    away_team = Column(String)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
