import { AnalyzeResponse, BotMoveResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function analyzePlayer(
  username: string,
  platform: string
): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, platform }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Analysis failed with status ${res.status}`
    );
  }

  return res.json();
}

export async function getBotMove(
  fen: string,
  playerUsername: string,
  platform?: string
): Promise<BotMoveResponse> {
  const res = await fetch(`${API_BASE}/bot/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      fen,
      player_username: playerUsername,
      platform,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Bot move request failed with status ${res.status}`
    );
  }

  return res.json();
}

export async function getPlayerProfile(
  username: string,
  platform?: string
): Promise<AnalyzeResponse | null> {
  const params = new URLSearchParams({ username });
  if (platform) params.set("platform", platform);

  const res = await fetch(`${API_BASE}/profile?${params.toString()}`);

  if (res.status === 404) return null;

  if (!res.ok) {
    throw new Error(`Profile fetch failed with status ${res.status}`);
  }

  return res.json();
}
