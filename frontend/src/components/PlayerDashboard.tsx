"use client";

import React from "react";
import { AnalyzeResponse } from "@/lib/types";
import {
  Crown,
  Sparkles,
  BookOpen,
  Award,
  Zap,
  Shield,
  Layers,
  Flame,
} from "lucide-react";
import ProfileCard from "@/components/ProfileCard";
import StatsGrid from "@/components/StatsGrid";
import StrengthWeakness from "@/components/StrengthWeakness";
import OpeningTable from "@/components/OpeningTable";
import CoachingPlan from "@/components/CoachingPlan";
import ChessBoardPanel from "@/components/ChessBoardPanel";

interface PlayerDashboardProps {
  data: AnalyzeResponse;
}

export default function PlayerDashboard({ data }: PlayerDashboardProps) {
  const { player, profile, coaching_plan = [] } = data;

  return (
    <main className="mx-auto max-w-[1800px] p-6 lg:p-8">
      {/* Split-View Layout: Left 60% / Right 40% */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* LEFT PANEL: Deep Psychological & Tactical Profile (7 cols on lg = ~58-60%) */}
        <section className="lg:col-span-7 space-y-6">
          {/* Header Card */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/60 p-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                    {player.username}
                  </h1>
                  <span className="rounded-full bg-primary/20 px-2.5 py-0.5 text-xs font-semibold text-primary-300 border border-primary/30 uppercase">
                    {player.platform}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <span className="flex items-center gap-1 font-medium text-accent">
                    <Flame className="w-4 h-4 text-accent" />
                    Archetype:
                  </span>
                  <span className="font-semibold text-white">
                    {profile.playstyle_archetype || "The Dynamic Pragmatist"}
                  </span>
                </div>
              </div>

              {/* GM Twin Callout */}
              {profile.comparable_gm && (
                <div className="flex items-center gap-3 bg-slate-950/60 border border-slate-800 rounded-xl px-4 py-2.5">
                  <Crown className="w-6 h-6 text-amber-400 shrink-0" />
                  <div>
                    <div className="text-[10px] uppercase font-semibold text-slate-400">
                      Grandmaster Twin
                    </div>
                    <div className="text-sm font-bold text-slate-100">
                      {profile.comparable_gm}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Key Metrics Grid */}
          <StatsGrid profile={profile} />

          {/* Executive Summary */}
          <ProfileCard
            title="Psychological & Tactical Summary"
            icon={<Sparkles className="w-4 h-4 text-accent" />}
            borderColor="border-accent/60"
          >
            <p className="text-sm text-slate-300 leading-relaxed">
              {profile.executive_summary ||
                "Player demonstrates a well-rounded baseline with sharp tactical instincts, occasionally overextending in closed pawn structures under positional duress."}
            </p>
          </ProfileCard>

          {/* Strengths & Fatal Vulnerabilities */}
          <ProfileCard
            title="Combat Profile & Blunder Analysis"
            icon={<Shield className="w-4 h-4 text-emerald-400" />}
            borderColor="border-emerald-500/50"
          >
            <StrengthWeakness
              strengths={profile.strengths || []}
              weaknesses={profile.weaknesses || []}
            />
          </ProfileCard>

          {/* Opening Repertoire Breakdown */}
          <ProfileCard
            title="Opening Repertoire & Outcomes"
            icon={<BookOpen className="w-4 h-4 text-primary" />}
            borderColor="border-primary/50"
          >
            <OpeningTable
              whiteOpenings={profile.opening_repertoire_white}
              blackOpenings={profile.opening_repertoire_black}
            />
          </ProfileCard>

          {/* AI Coaching Plan */}
          <ProfileCard
            title="Grandmaster Prescription: 3-Step Master Plan"
            icon={<Award className="w-4 h-4 text-violet-400" />}
            borderColor="border-violet-500/50"
          >
            <CoachingPlan
              steps={coaching_plan}
              priorities={profile.improvement_priorities || []}
            />
          </ProfileCard>
        </section>

        {/* RIGHT PANEL: Playable Clone Bot (5 cols on lg = ~40-42%) */}
        <aside className="lg:col-span-5 sticky top-20">
          <ChessBoardPanel
            playerUsername={player.username}
            playerRating={profile.estimated_elo}
            playstyleArchetype={profile.playstyle_archetype}
          />
        </aside>
      </div>
    </main>
  );
}

