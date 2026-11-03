export interface OpeningStats {
  eco: string;
  name: string;
  games: number;
  wins: number;
  draws: number;
  losses: number;
  win_rate: number;
  draw_rate: number;
  loss_rate: number;
}

export interface PlayerProfile {
  username: string;
  platform: string;
  estimated_elo: number;
  games_analyzed: number;
  avg_centipawn_loss: number;
  blunder_rate: number;
  playstyle_archetype: string;
  comparable_gm: string;
  executive_summary: string;
  strengths: string[];
  weaknesses: string[];
  opening_repertoire_white: OpeningStats[];
  opening_repertoire_black: OpeningStats[];
  improvement_priorities: string[];
}

export interface PlayerResponse {
  username: string;
  platform: string;
  rating: number;
  title?: string;
  avatar_url?: string;
}

export interface GameResponse {
  id: string;
  white: string;
  black: string;
  result: string;
  time_control: string;
  date: string;
  pgn: string;
  opening: string;
  eco: string;
}

export interface AnalyzeResponse {
  player: PlayerResponse;
  profile: PlayerProfile;
  coaching_plan: CoachingStep[];
}

export interface CoachingStep {
  step: number;
  title: string;
  description: string;
}

export interface BotMoveRequest {
  fen: string;
  player_username: string;
  platform?: string;
}

export interface BotMoveResponse {
  move: string;
  fen_after: string;
  explanation: string;
  source: "opening_book" | "stockfish_clone" | "endgame_table";
  evaluation: number;
}
