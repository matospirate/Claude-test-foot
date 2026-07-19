from typing import Optional
from pydantic import BaseModel, ConfigDict


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    country: Optional[str] = None


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    known_name: Optional[str] = None
    nationality: Optional[str] = None
    primary_position: Optional[str] = None


class CompetitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    season_name: str
    gender: Optional[str] = None
    country: Optional[str] = None


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    match_date: Optional[str] = None
    match_week: Optional[int] = None
    stadium: Optional[str] = None
    home_team: TeamOut
    away_team: TeamOut
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    competition: CompetitionOut


class StandingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    team_name: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    position: Optional[int] = None


class LeagueMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    match_date: Optional[str] = None
    matchday: Optional[int] = None
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None


class PlayerMatchStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    minutes_played: int
    goals: int
    own_goals: int
    assists: int
    shots: int
    shots_on_target: int
    xg: float
    xa: float
    key_passes: int
    passes_attempted: int
    passes_completed: int
    progressive_passes: int
    through_balls: int
    crosses_attempted: int
    crosses_completed: int
    touches: int
    dribbles_attempted: int
    dribbles_completed: int
    carries: int
    progressive_carries: int
    dispossessed: int
    tackles: int
    tackles_won: int
    interceptions: int
    clearances: int
    blocks: int
    pressures: int
    fouls_committed: int
    fouls_won: int
    yellow_cards: int
    red_cards: int
    ball_recoveries: int


class ShotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    minute: Optional[int] = None
    second: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    end_x: Optional[float] = None
    end_y: Optional[float] = None
    body_part: Optional[str] = None
    technique: Optional[str] = None
    shot_type: Optional[str] = None
    outcome: Optional[str] = None
    xg: Optional[float] = None
    is_first_time: bool = False
    under_pressure: bool = False
    player_id: Optional[int] = None
    team_id: Optional[int] = None
