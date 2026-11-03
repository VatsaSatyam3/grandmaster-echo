"use client";

import React, { useState, useCallback } from "react";
import {
  Search,
  ChevronDown,
  Crown,
  Zap,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { analyzePlayer } from "@/lib/api";
import { AnalyzeResponse } from "@/lib/types";
import PlayerDashboard from "@/components/PlayerDashboard";
import LoadingSpinner from "@/components/LoadingSpinner";

const PLATFORMS = [
  { value: "chesscom", label: "Chess.com" },
  { value: "lichess", label: "Lichess" },
];

export default function HomePage() {
  const [username, setUsername] = useState("");
  const [platform, setPlatform] = useState("chesscom");
  const [platformOpen, setPlatformOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const handleAnalyze = useCallback(async () => {
    const trimmed = username.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzePlayer(trimmed, platform);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred."
      );
    } finally {
      setLoading(false);
    }
  }, [username, platform]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleAnalyze();
  };

  // If we have a result, show the dashboard
  if (result) {
    return (
      <div className="min-h-screen bg-slate-950">
        {/* Slim top bar to go back */}
        <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-[1800px] items-center justify-between px-6 py-3">
            <button
              onClick={() => setResult(null)}
              className="flex items-center gap-2 text-sm font-medium text-slate-400 transition-colors hover:text-white"
            >
              <Crown className="h-5 w-5 text-primary" />
              <span className="hidden sm:inline">Grandmaster Echo</span>
            </button>
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <span className="font-semibold text-white">
                {result.player.username}
              </span>
              <span className="rounded bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary-300">
                {result.player.platform === "chesscom"
                  ? "Chess.com"
                  : "Lichess"}
              </span>
            </div>
          </div>
        </header>
        <PlayerDashboard data={result} />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4">
      {/* Background gradient effects */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[900px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[400px] w-[600px] translate-x-1/4 translate-y-1/4 rounded-full bg-accent/5 blur-[100px]" />
      </div>

      {/* Hero content */}
      <div className="relative z-10 w-full max-w-2xl animate-fade-in text-center">
        {/* Logo / icon */}
        <div className="mb-6 flex items-center justify-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/20 ring-1 ring-primary/30">
            <Crown className="h-7 w-7 text-primary-300" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl font-extrabold tracking-tight text-white sm:text-6xl">
          Grandmaster{" "}
          <span className="bg-gradient-to-r from-primary-400 to-accent bg-clip-text text-transparent">
            Echo
          </span>
        </h1>

        {/* Tagline */}
        <p className="mt-4 text-lg text-slate-400 sm:text-xl">
          Clone any chess player.{" "}
          <span className="text-slate-300">Analyze their soul.</span>
        </p>

        {/* Features chips */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {[
            { icon: Zap, label: "Opening Repertoire" },
            { icon: Sparkles, label: "AI Coaching Plan" },
            { icon: Crown, label: "Play vs Clone Bot" },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/40 px-3 py-1.5 text-xs text-slate-400"
            >
              <Icon className="h-3.5 w-3.5 text-primary-400" />
              {label}
            </div>
          ))}
        </div>

        {/* Input area */}
        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
          {/* Platform selector */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setPlatformOpen(!platformOpen)}
              className={cn(
                "flex h-12 items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 text-sm text-slate-300 transition-colors hover:border-slate-600",
                platformOpen && "border-primary/50"
              )}
            >
              {PLATFORMS.find((p) => p.value === platform)?.label}
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-slate-500 transition-transform",
                  platformOpen && "rotate-180"
                )}
              />
            </button>
            {platformOpen && (
              <div className="absolute left-0 top-14 z-20 w-full min-w-[140px] overflow-hidden rounded-xl border border-slate-700 bg-slate-800 shadow-xl">
                {PLATFORMS.map((p) => (
                  <button
                    key={p.value}
                    onClick={() => {
                      setPlatform(p.value);
                      setPlatformOpen(false);
                    }}
                    className={cn(
                      "block w-full px-4 py-2.5 text-left text-sm transition-colors hover:bg-slate-700",
                      platform === p.value
                        ? "text-primary-300"
                        : "text-slate-300"
                    )}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Username input */}
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Enter chess username..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={handleKeyDown}
              className="h-12 w-full rounded-xl border border-slate-700 bg-slate-800/80 pl-11 pr-4 text-sm text-white placeholder-slate-500 transition-colors focus:border-primary/50 focus:ring-0 sm:min-w-[300px]"
            />
          </div>

          {/* Analyze button */}
          <button
            onClick={handleAnalyze}
            disabled={loading || !username.trim()}
            className={cn(
              "h-12 rounded-xl bg-primary px-8 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:bg-primary-600 hover:shadow-primary/40 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
            )}
          >
            Analyze Player
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mt-4 animate-fade-in rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        )}
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm">
          <LoadingSpinner username={username} />
        </div>
      )}
    </div>
  );
}
