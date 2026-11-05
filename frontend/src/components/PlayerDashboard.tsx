"use client";

import React from "react";
import { AnalyzeResponse } from "@/lib/types";
import ProfileCard from "@/components/ProfileCard";
import StatsGrid from "@/components/StatsGrid";
import StrengthWeakness from "@/components/StrengthWeakness";
import OpeningTable from "@/components/OpeningTable";
import CoachingPlan from "@/components/CoachingPlan";
import ChessBoardPanel from "@/components/ChessBoardPanel";
import AnalysisMeta from "@/components/AnalysisMeta";

interface PlayerDashboardProps {
  data: AnalyzeResponse;
}

function MetaCell({
  label,
  value,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="border border-term-line bg-term-raised px-3 py-2.5">
      <div className="tlabel">{label}</div>
      <div className="mt-1 font-mono text-[15px] text-term-text">{value}</div>
      {sub && (
        <div className="mt-0.5 font-mono text-[9px] text-term-faint">{sub}</div>
      )}
    </div>
  );
}

function StatusRow({
  label,
  value,
  ok = true,
}: {
  label: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <li className="flex items-center justify-between gap-3">
      <span className="text-term-faint">{label}</span>
      <span className="flex items-center gap-2">
        <span className="text-term-text">{value}</span>
        <span
          aria-hidden
          className={ok ? "text-term-green" : "text-term-amber"}
        >
          {ok ? "●" : "▲"}
        </span>
      </span>
    </li>
  );
}

export default function PlayerDashboard({ data }: PlayerDashboardProps) {
  const { player, profile, coaching_plan = [] } = data;
  const platformLabel =
    player.platform === "chesscom" ? "CHESS.COM" : "LICHESS";

  const evalScore = data.evals?.overall;
  const latency = data.pipeline_ms?.total_ms ?? data.evals?.latency_ms;
  const citations = data.citations ?? [];

  return (
    <main className="mx-auto max-w-[1440px] px-5 py-6 lg:px-8">
      {/* Dossier summary */}
      <section className="border border-term-line bg-term-panel">
        <div className="panel-bar flex items-center justify-between px-3 py-2 font-mono text-[10px] tracking-wider">
          <div className="flex items-center gap-2 text-term-muted">
            <span className="text-term-green">▸</span>
            <span>PLAYER DOSSIER</span>
            <span className="text-term-faint">/</span>
            <span>{platformLabel}</span>
          </div>
          <span className="text-term-faint">
            {profile.games_analyzed} GAMES · SESSION 01
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12">
          <div className="border-b border-term-line p-4 lg:col-span-8 lg:border-b-0 lg:border-r lg:p-6">
            <p className="tlabel">PLAYER</p>
            <h1 className="mt-2 font-mono text-3xl tracking-tight text-term-text lg:text-4xl">
              {player.username}
            </h1>
            <p className="mt-2 font-mono text-[12px] text-term-green">
              // {profile.playstyle_archetype || "UNCLASSIFIED"}
            </p>

            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
              <MetaCell
                label="EST. ELO"
                value={profile.estimated_elo}
                sub="engine-derived"
              />
              <MetaCell
                label="GM TWIN"
                value={profile.comparable_gm || "—"}
                sub="style match"
              />
              <MetaCell
                label="SAMPLE"
                value={profile.games_analyzed}
                sub="games parsed"
              />
            </div>
          </div>

          <div className="p-4 lg:col-span-4 lg:p-6">
            <p className="tlabel">SYSTEM STATUS</p>
            <ul className="mt-3 space-y-2 font-mono text-[10px] tracking-wide">
              <StatusRow label="STOCKFISH" value="ONLINE" />
              <StatusRow
                label="RAG RETRIEVAL"
                value={
                  data.rag_enabled ? `${citations.length} HITS` : "FALLBACK"
                }
                ok={data.rag_enabled}
              />
              <StatusRow
                label="GUARDRAILS"
                value={data.guardrails?.passed ? "PASS" : "REVIEW"}
                ok={data.guardrails?.passed ?? false}
              />
              <StatusRow
                label="EVAL SCORE"
                value={
                  evalScore !== undefined ? `${Math.round(evalScore * 100)}%` : "N/A"
                }
              />
              <StatusRow
                label="LATENCY"
                value={latency !== undefined ? `${latency.toFixed(0)} MS` : "N/A"}
              />
            </ul>
          </div>
        </div>
      </section>

      <div className="mt-4 grid grid-cols-1 items-start gap-4 lg:grid-cols-12">
        {/* Report */}
        <div className="space-y-4 lg:col-span-8">
          <StatsGrid profile={profile} />

          <ProfileCard title="EXECUTIVE SUMMARY" kicker="AGENT OUTPUT">
            <p className="text-[13px] leading-6 text-term-text/80">
              {profile.executive_summary ||
                "The sample is too small to support a confident narrative. Play more rated games and run the dossier again."}
            </p>
          </ProfileCard>

          <ProfileCard title="COMBAT PROFILE" kicker="STRENGTHS / FAILURES">
            <StrengthWeakness
              strengths={profile.strengths || []}
              weaknesses={profile.weaknesses || []}
            />
          </ProfileCard>

          <ProfileCard title="OPENING REPERTOIRE" kicker="ECO / OUTCOMES">
            <OpeningTable
              whiteOpenings={profile.opening_repertoire_white}
              blackOpenings={profile.opening_repertoire_black}
            />
          </ProfileCard>

          <ProfileCard title="PRESCRIPTION" kicker="3-STEP PLAN">
            <CoachingPlan
              steps={coaching_plan}
              priorities={profile.improvement_priorities || []}
            />
          </ProfileCard>

          <ProfileCard title="SOURCES & CONFIDENCE" kicker="RAG / EVALS">
            <AnalysisMeta
              citations={data.citations}
              evals={data.evals}
              guardrails={data.guardrails}
              ragEnabled={data.rag_enabled}
              pipelineMs={data.pipeline_ms}
            />
          </ProfileCard>
        </div>

        {/* Clone console */}
        <aside className="lg:col-span-4 lg:sticky lg:top-16">
          <ChessBoardPanel
            playerUsername={player.username}
            playerRating={profile.estimated_elo}
            playstyleArchetype={profile.playstyle_archetype}
          />
        </aside>
      </div>

      <footer className="mt-8 flex flex-col gap-1 border-t border-term-line pt-3 font-mono text-[10px] text-term-faint sm:flex-row sm:items-center sm:justify-between">
        <span>GME · GEMINI / QDRANT / LANGGRAPH / STOCKFISH 16</span>
        <span className="tracking-wider">{profile.games_analyzed} GAMES ANALYSED</span>
      </footer>
    </main>
  );
}
