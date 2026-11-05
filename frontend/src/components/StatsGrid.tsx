"use client";

import React from "react";
import { PlayerProfile } from "@/lib/types";

interface StatsGridProps {
  profile: PlayerProfile;
}

export default function StatsGrid({ profile }: StatsGridProps) {
  const stats = [
    {
      label: "EST_ELO",
      value: profile.estimated_elo,
      sub: "engine-derived",
    },
    {
      label: "GAMES",
      value: profile.games_analyzed,
      sub: "parsed sample",
    },
    {
      label: "ACPL",
      value: profile.avg_centipawn_loss.toFixed(1),
      sub: "lower is better",
    },
    {
      label: "BLUNDER_RATE",
      value: profile.blunder_rate.toFixed(2),
      sub: "per game",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="border border-term-line bg-term-panel px-3 py-3"
        >
          <div className="tlabel">{stat.label}</div>
          <div className="tnum mt-2 text-2xl leading-none text-term-text">
            {stat.value}
          </div>
          <div className="mt-1 font-mono text-[9px] text-term-faint">
            {stat.sub}
          </div>
        </div>
      ))}
    </div>
  );
}
