"use client";

import React from "react";
import {
  Star,
  BarChart3,
  Crosshair,
  AlertTriangle,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { PlayerProfile } from "@/lib/types";

interface StatsGridProps {
  profile: PlayerProfile;
}

interface StatItem {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

export default function StatsGrid({ profile }: StatsGridProps) {
  const stats: StatItem[] = [
    {
      label: "Estimated Elo",
      value: profile.estimated_elo,
      icon: <Star className="h-5 w-5" />,
      color: "text-accent",
    },
    {
      label: "Games Analyzed",
      value: profile.games_analyzed,
      icon: <BarChart3 className="h-5 w-5" />,
      color: "text-primary-300",
    },
    {
      label: "Avg Centipawn Loss",
      value: profile.avg_centipawn_loss.toFixed(1),
      icon: <Crosshair className="h-5 w-5" />,
      color: "text-emerald-400",
    },
    {
      label: "Blunder Rate",
      value: `${(profile.blunder_rate * 100).toFixed(1)}%`,
      icon: <AlertTriangle className="h-5 w-5" />,
      color: "text-rose-400",
    },
    {
      label: "Comparable GM",
      value: profile.comparable_gm,
      icon: <Users className="h-5 w-5" />,
      color: "text-violet-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="glass group flex flex-col items-center rounded-xl p-4 text-center transition-all duration-200 hover:border-slate-600/30"
        >
          <div
            className={cn(
              "mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-700/40 transition-colors",
              stat.color
            )}
          >
            {stat.icon}
          </div>
          <div className={cn("text-xl font-bold text-white", stat.color)}>
            {stat.value}
          </div>
          <div className="mt-1 text-xs text-slate-500">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
