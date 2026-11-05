export interface OpeningStats {
  eco: string;
  name: string;
  games: number;
  count?: number;
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
  summary_text?: string;
  strengths: string[];
  weaknesses: string[];
  opening_repertoire_white: OpeningStats[];
  opening_repertoire_black: OpeningStats[];
  improvement_priorities: string[];
}

export interface PlayerResponse {
  id?: number;
  username: string;
  platform: string;
  current_rating?: number;
  rating?: number;
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

export interface RAGCitation {
  game_id: string;
  opening: string;
  eco: string;
  result: string;
  played_as: string;
  score: number;
  excerpt: string;
}

export interface GuardrailIssue {
  rule: string;
  message: string;
  severity: "info" | "warning" | "error";
  corrected: boolean;
}

export interface GuardrailResult {
  passed: boolean;
  checks_run: number;
  issues: GuardrailIssue[];
}

export interface EvalMetrics {
  overall: number;
  schema_validity: number;
  elo_alignment: number;
  opening_grounding: number;
  citation_coverage: number;
  guardrail_pass: number;
  latency_ms: number;
}

export interface AnalyzeResponse {
  player: PlayerResponse;
  profile: PlayerProfile;
  games_analyzed?: number;
  coaching_plan: CoachingStep[];
  openings?: OpeningStats[];
  citations?: RAGCitation[];
  rag_enabled?: boolean;
  guardrails?: GuardrailResult;
  evals?: EvalMetrics;
  pipeline_ms?: Record<string, number>;
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

export type StreamStage =
  | "queued"
  | "ingesting"
  | "parsing"
  | "engine"
  | "rag_indexing"
  | "rag_retrieval"
  | "agents"
  | "guardrails"
  | "evals";
