const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API error ${res.status} on ${path}`);
  }
  return res.json();
}

export type League = { code: string; name: string; seasons: string[] };
export type Standing = {
  team_name: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  position: number;
};
export type LeagueMatch = {
  match_date: string | null;
  matchday: number | null;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
};

export type Competition = {
  id: number;
  name: string;
  season_name: string;
  gender: string | null;
  country: string | null;
  matches_ingested: number;
};

export type CompMatch = {
  id: number;
  match_date: string;
  match_week: number | null;
  stadium: string | null;
  home_team: { id: number; name: string };
  away_team: { id: number; name: string };
  home_score: number | null;
  away_score: number | null;
};

export type Leader = {
  player_id: number;
  player_name: string;
  team_name: string;
  value: number;
  minutes: number;
  matches: number;
};

export type PlayerProfile = {
  id: number;
  name: string;
  known_name: string | null;
  nationality: string | null;
  primary_position: string | null;
  teams_competitions: { team: string; competition: string; season: string }[];
  career_totals: Record<string, number>;
  per_90: Record<string, number>;
};

export type PlayerMatch = {
  match_id: number;
  date: string;
  competition: string;
  opponent: string;
  score: string;
  minutes_played: number;
  goals: number;
  assists: number;
  xg: number;
  xa: number;
  shots: number;
  passes_completed: number;
  passes_attempted: number;
};

export type Shot = {
  id?: number;
  player_id?: number | null;
  player_name?: string | null;
  team_id?: number;
  minute: number | null;
  x: number | null;
  y: number | null;
  end_x: number | null;
  end_y: number | null;
  body_part: string | null;
  technique: string | null;
  shot_type: string | null;
  outcome: string | null;
  xg: number;
};

export type MatchDetail = {
  id: number;
  date: string;
  stadium: string | null;
  competition: { id: number; name: string; season: string };
  home_team: TeamSide;
  away_team: TeamSide;
  goals: { minute: number; player: string | null; team_id: number; xg: number }[];
};

export type TeamSide = {
  id: number;
  name: string;
  score: number | null;
  stats: {
    shots: number;
    shots_on_target: number;
    xg: number;
    possession_pct: number | null;
    ppda: number | null;
    passes_completed: number;
    passes_attempted: number;
    fouls: number;
  } | null;
  lineup: {
    player_id: number;
    name: string;
    position: string | null;
    jersey_number: number | null;
    is_starter: boolean;
    minutes_played: number;
  }[];
};

export type TeamProfile = {
  id: number;
  name: string;
  country: string | null;
  squad: { player_id: number; name: string; appearances: number; minutes: number }[];
  matches: {
    match_id: number;
    date: string;
    competition: string;
    home_team: string;
    away_team: string;
    home_score: number | null;
    away_score: number | null;
  }[];
};

export type SearchResult = {
  players: { id: number; name: string; nationality: string | null }[];
  teams: { id: number; name: string; country: string | null }[];
};

export type CompareResult = {
  metrics: string[];
  players: {
    player_id: number;
    name: string;
    minutes_played: number;
    matches: number;
    per_90: Record<string, number>;
  }[];
};

export const api = {
  leagues: () => apiFetch<League[]>("/api/leagues"),
  standings: (code: string, season: string) =>
    apiFetch<Standing[]>(`/api/leagues/${code}/standings?season=${season}`),
  leagueMatches: (code: string, season: string) =>
    apiFetch<LeagueMatch[]>(`/api/leagues/${code}/matches?season=${season}`),

  competitions: () => apiFetch<Competition[]>("/api/competitions"),
  competitionMatches: (id: number) => apiFetch<CompMatch[]>(`/api/competitions/${id}/matches`),
  competitionStandings: (id: number) =>
    apiFetch<
      { team: string; played: number; won: number; drawn: number; lost: number;
        gf: number; ga: number; points: number; goal_diff: number; position: number }[]
    >(`/api/competitions/${id}/standings`),
  competitionLeaders: (id: number, stat: string, limit = 10) =>
    apiFetch<Leader[]>(`/api/competitions/${id}/leaders?stat=${stat}&limit=${limit}`),

  player: (id: number) => apiFetch<PlayerProfile>(`/api/players/${id}`),
  playerMatches: (id: number) => apiFetch<PlayerMatch[]>(`/api/players/${id}/matches`),
  playerShots: (id: number) => apiFetch<Shot[]>(`/api/players/${id}/shots`),

  team: (id: number) => apiFetch<TeamProfile>(`/api/teams/${id}`),
  teamMatchStats: (id: number) =>
    apiFetch<
      { match_id: number; date: string; shots: number; shots_on_target: number; xg: number;
        possession_pct: number | null; ppda: number | null;
        passes_completed: number; passes_attempted: number }[]
    >(`/api/teams/${id}/match-stats`),

  match: (id: number) => apiFetch<MatchDetail>(`/api/matches/${id}`),
  matchShots: (id: number) => apiFetch<Shot[]>(`/api/matches/${id}/shots`),
  matchPassNetwork: (id: number, teamId: number) =>
    apiFetch(`/api/matches/${id}/pass-network?team_id=${teamId}`),

  compare: (playerIds: number[]) =>
    apiFetch<CompareResult>(`/api/compare?player_ids=${playerIds.join(",")}`),

  search: (q: string) => apiFetch<SearchResult>(`/api/search?q=${encodeURIComponent(q)}`),
};
