"use client";

import React, { useState, useCallback } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { analyzePlayer, streamAnalyzePlayer } from "@/lib/api";
import { AnalyzeResponse, StreamStage } from "@/lib/types";
import PlayerDashboard from "@/components/PlayerDashboard";
import LoadingSpinner from "@/components/LoadingSpinner";

const PLATFORMS = [
  { value: "chesscom", label: "chess.com" },
  { value: "lichess", label: "lichess" },
];

const PIPELINE = [
  { no: "01", label: "INGEST", body: "Fetch up to 200 recent games" },
  { no: "02", label: "ENGINE", body: "Stockfish 16 position audit" },
  { no: "03", label: "RETRIEVE", body: "Qdrant semantic move search" },
  { no: "04", label: "SYNTHESIZE", body: "LangGraph analyst agents" },
  { no: "05", label: "VERIFY", body: "Guardrails + automated evals" },
];

function HeaderStatus({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-term-faint">{label}</span>
      <span className="text-term-text">{value}</span>
      <span className="h-1 w-1 bg-term-green" aria-hidden />
    </div>
  );
}

export default function HomePage() {
  const [username, setUsername] = useState("");
  const [platform, setPlatform] = useState("chesscom");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<StreamStage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const handleAnalyze = useCallback(async () => {
    const trimmed = username.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setStage("queued");

    try {
      const data = await streamAnalyzePlayer(trimmed, platform, (next) =>
        setStage(next)
      );
      setResult(data);
    } catch {
      // Some proxies buffer SSE; fall back to the REST endpoint.
      try {
        const data = await analyzePlayer(trimmed, platform);
        setResult(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unexpected pipeline failure."
        );
      }
    } finally {
      setLoading(false);
      setStage(null);
    }
  }, [username, platform]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    handleAnalyze();
  };

  if (result) {
    return (
      <div className="min-h-screen bg-term-bg">
        <header className="sticky top-0 z-50 border-b border-term-line bg-term-bg/95 backdrop-blur-sm">
          <div className="mx-auto flex h-12 max-w-[1440px] items-center justify-between px-5 font-mono text-[11px] lg:px-8">
            <button
              onClick={() => setResult(null)}
              className="group flex items-center gap-2 text-term-muted transition-colors hover:text-term-text"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span className="tracking-wider">GME://DOSSIER</span>
            </button>
            <div className="flex items-center gap-4 text-term-faint">
              <span>
                USER <span className="text-term-text">{result.player.username}</span>
              </span>
              <span className="hidden sm:inline">
                SRC{" "}
                <span className="text-term-text">
                  {result.player.platform === "chesscom" ? "CHESS.COM" : "LICHESS"}
                </span>
              </span>
              <span className="flex items-center gap-1.5 text-term-green">
                <span className="h-1 w-1 bg-term-green" aria-hidden />
                LIVE
              </span>
            </div>
          </div>
        </header>
        <PlayerDashboard data={result} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-term-bg">
      <header className="border-b border-term-line">
        <div className="mx-auto flex h-12 max-w-[1440px] items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3 font-mono text-[11px] tracking-wider">
            <span className="text-term-green">●</span>
            <span className="text-term-text">GME://ANALYSIS-TERMINAL</span>
            <span className="hidden text-term-faint sm:inline">v1.0.0</span>
          </div>

          <div className="hidden items-center gap-5 font-mono text-[10px] tracking-wider md:flex">
            <HeaderStatus label="ENGINE" value="STOCKFISH 16" />
            <HeaderStatus label="VECTOR" value="QDRANT" />
            <HeaderStatus label="MODEL" value="GEMINI 2.5" />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-5 lg:px-8">
        <section className="grid grid-cols-1 gap-8 py-10 lg:grid-cols-12 lg:gap-10 lg:py-16">
          <div className="animate-fade-up lg:col-span-8">
            <p className="tlabel text-term-green">
              $ gme analyze --player --platform
            </p>

            <h1 className="mt-5 font-mono text-3xl font-medium leading-[1.1] tracking-tight text-term-text sm:text-4xl lg:text-[3.25rem]">
              Chess analysis,
              <br />
              <span className="text-term-muted">instrumented.</span>
            </h1>

            <p className="mt-5 max-w-2xl text-[13px] leading-6 text-term-muted">
              Grandmaster Echo ingests a player&apos;s recent games, evaluates
              every position with Stockfish, retrieves recurring tactical
              patterns from a Qdrant vector index, and runs a LangGraph analyst
              graph whose output is checked by deterministic guardrails and
              scored against the engine.
            </p>

            <form onSubmit={handleSubmit} className="mt-8 max-w-3xl">
              <div className="border border-term-line bg-term-panel">
                <div className="panel-bar flex items-center justify-between px-3 py-2 font-mono text-[10px] tracking-wider text-term-muted">
                  <div className="flex items-center gap-2">
                    <span className="text-term-green">▸</span>
                    <span>INPUT</span>
                    <span className="text-term-faint">/</span>
                    <span>PLAYER LOOKUP</span>
                  </div>
                  <div className="flex items-center gap-1.5" aria-hidden>
                    <span className="h-1.5 w-1.5 border border-term-faint" />
                    <span className="h-1.5 w-1.5 border border-term-faint" />
                    <span className="h-1.5 w-1.5 border border-term-faint" />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row">
                  <div className="flex border-b border-term-line sm:border-b-0 sm:border-r">
                    {PLATFORMS.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setPlatform(option.value)}
                        className={cn(
                          "px-3 py-3 font-mono text-[10px] tracking-wider transition-colors",
                          platform === option.value
                            ? "bg-term-raised text-term-green"
                            : "text-term-faint hover:text-term-text"
                        )}
                      >
                        [{option.label}]
                      </button>
                    ))}
                  </div>

                  <label htmlFor="username" className="sr-only">
                    Chess username
                  </label>
                  <div className="flex flex-1 items-center gap-2 px-3">
                    <span className="font-mono text-xs text-term-green">$</span>
                    <input
                      id="username"
                      type="text"
                      autoComplete="off"
                      spellCheck={false}
                      placeholder="enter username"
                      value={username}
                      onChange={(event) => setUsername(event.target.value)}
                      className="h-11 w-full border-0 bg-transparent font-mono text-[13px] text-term-text placeholder:text-term-faint focus:outline-none"
                    />
                    <span className="hidden h-4 w-1.5 animate-blink bg-term-green sm:block" aria-hidden />
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !username.trim()}
                    className="group flex h-11 items-center justify-center gap-2 border-t border-term-line bg-term-green px-6 font-mono text-[11px] font-semibold tracking-wider text-term-bg transition-colors hover:bg-[#8bf0ba] disabled:cursor-not-allowed disabled:bg-term-line disabled:text-term-faint sm:border-t-0 sm:border-l sm:border-term-line"
                  >
                    RUN
                    <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </button>
                </div>
              </div>
            </form>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[10px] text-term-faint">
              <span>NO AUTH REQUIRED</span>
              <span aria-hidden>·</span>
              <span>~200 GAMES / RUN</span>
              <span aria-hidden>·</span>
              <span>SSE STREAM ENABLED</span>
            </div>

            {error && (
              <div className="mt-5 border border-term-red/40 bg-term-red/5 px-3 py-2 font-mono text-[11px] text-term-red">
                [ERROR] {error}
              </div>
            )}
          </div>

          <aside className="space-y-4 lg:col-span-4">
            <div className="border border-term-line bg-term-panel">
              <div className="panel-bar flex items-center justify-between px-3 py-2 font-mono text-[10px] tracking-wider">
                <span className="text-term-muted">PIPELINE</span>
                <span className="text-term-faint">5 STAGES</span>
              </div>
              <ol>
                {PIPELINE.map((item) => (
                  <li
                    key={item.no}
                    className="row-line flex items-baseline gap-3 px-3 py-2.5"
                  >
                    <span className="font-mono text-[10px] text-term-green">
                      {item.no}
                    </span>
                    <div>
                      <div className="font-mono text-[11px] tracking-wider text-term-text">
                        {item.label}
                      </div>
                      <div className="mt-0.5 text-[11px] text-term-muted">
                        {item.body}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="border border-term-line bg-term-panel">
              <div className="panel-bar px-3 py-2 font-mono text-[10px] tracking-wider text-term-muted">
                RUNTIME
              </div>
              <dl className="divide-y divide-term-line font-mono text-[10px]">
                {[
                  ["DB", "POSTGRES 16"],
                  ["VECTOR", "QDRANT"],
                  ["LLM", "GEMINI / OPENAI"],
                  ["EVALS", "STOCKFISH GROUNDED"],
                ].map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between px-3 py-2">
                    <dt className="text-term-faint">{key}</dt>
                    <dd className="text-term-text">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </aside>
        </section>
      </main>

      <footer className="border-t border-term-line">
        <div className="mx-auto flex h-10 max-w-[1440px] items-center justify-between px-5 font-mono text-[10px] text-term-faint lg:px-8">
          <span>GME · OPEN-SOURCE CHESS ANALYSIS</span>
          <span className="tracking-wider">NEXT.JS / FASTAPI / LANGGRAPH</span>
        </div>
      </footer>

      {loading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-term-bg/95 backdrop-blur-sm">
          <LoadingSpinner username={username} stage={stage} />
        </div>
      )}
    </div>
  );
}
