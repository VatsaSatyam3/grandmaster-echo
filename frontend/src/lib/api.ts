import { AnalyzeResponse, BotMoveResponse, StreamStage } from "./types";

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

/**
 * Consume the backend SSE pipeline. Progress stages arrive while the
 * multi-agent graph runs; the resolved value is the final analysis.
 */
export async function streamAnalyzePlayer(
  username: string,
  platform: string,
  onProgress?: (stage: StreamStage, payload: Record<string, unknown>) => void
): Promise<AnalyzeResponse> {
  const params = new URLSearchParams({ platform });
  const res = await fetch(
    `${API_BASE}/stream/analyze/${encodeURIComponent(username)}?${params.toString()}`,
    { headers: { Accept: "text/event-stream" } }
  );

  if (!res.ok || !res.body) {
    throw new Error(`Stream failed with status ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const dataLine = frame
        .split("\n")
        .find((line) => line.startsWith("data: "));
      if (!dataLine) continue;

      const payload = JSON.parse(dataLine.slice(6));

      if (payload.event === "progress") {
        onProgress?.(payload.stage as StreamStage, payload);
      } else if (payload.event === "result") {
        return payload.data as AnalyzeResponse;
      } else if (payload.event === "error") {
        throw new Error(payload.message || "Streaming analysis failed");
      }
    }
  }

  throw new Error("Stream ended before a result was produced");
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
