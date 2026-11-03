"use client";

import React, { useState } from "react";
import { OpeningStats } from "@/lib/types";
import { BookOpen, Trophy, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface OpeningTableProps {
  whiteOpenings?: OpeningStats[];
  blackOpenings?: OpeningStats[];
  generalOpenings?: OpeningStats[];
}

export default function OpeningTable({
  whiteOpenings = [],
  blackOpenings = [],
  generalOpenings = [],
}: OpeningTableProps) {
  const [activeTab, setActiveTab] = useState<"white" | "black">("white");
  const [sortBy, setSortBy] = useState<"games" | "win_rate">("games");

  // Fallback if white/black specific repertoire is empty
  const activeList =
    activeTab === "white"
      ? whiteOpenings.length > 0
        ? whiteOpenings
        : generalOpenings
      : blackOpenings.length > 0
      ? blackOpenings
      : generalOpenings;

  const sortedOpenings = [...activeList].sort((a, b) => {
    if (sortBy === "win_rate") {
      return (b.win_rate || 0) - (a.win_rate || 0);
    }
    const gamesA = a.games ?? (a as any).count ?? 0;
    const gamesB = b.games ?? (b as any).count ?? 0;
    return gamesB - gamesA;
  });

  return (
    <div className="w-full">
      {/* Tab Switcher & Sorting Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("white")}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              activeTab === "white"
                ? "bg-slate-100 text-slate-900 shadow"
                : "text-slate-400 hover:text-slate-200"
            )}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-slate-200 border border-slate-400" />
            As White ({whiteOpenings.length || generalOpenings.length})
          </button>
          <button
            onClick={() => setActiveTab("black")}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              activeTab === "black"
                ? "bg-slate-800 text-white shadow border border-slate-700"
                : "text-slate-400 hover:text-slate-200"
            )}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-slate-900 border border-slate-600" />
            As Black ({blackOpenings.length || generalOpenings.length})
          </button>
        </div>

        <button
          onClick={() => setSortBy((prev) => (prev === "games" ? "win_rate" : "games"))}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg bg-slate-800/40 hover:bg-slate-800 transition-colors"
        >
          <ArrowUpDown className="w-3.5 h-3.5" />
          <span>Sort: {sortBy === "games" ? "Most Played" : "Highest Win%"}</span>
        </button>
      </div>

      {sortedOpenings.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-sm">
          No opening data available for this side.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800/80">
                <th className="pb-2.5 font-medium pl-1">ECO</th>
                <th className="pb-2.5 font-medium">Opening Name</th>
                <th className="pb-2.5 font-medium text-center">Games</th>
                <th className="pb-2.5 font-medium text-right pr-2">Outcome Distribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {sortedOpenings.map((opening) => {
                const winPct = Math.round((opening.win_rate || 0) * 100);
                const drawPct = Math.round((opening.draw_rate || 0) * 100);
                const lossPct = Math.max(0, 100 - winPct - drawPct);

                return (
                  <tr
                    key={opening.eco + opening.name}
                    className="hover:bg-slate-800/30 transition-colors group"
                  >
                    <td className="py-2.5 pl-1 font-mono text-xs font-semibold text-primary-300">
                      {opening.eco || "N/A"}
                    </td>
                    <td className="py-2.5 font-medium text-slate-200 max-w-xs truncate">
                      {opening.name || "Custom Opening"}
                    </td>
                    <td className="py-2.5 text-center text-slate-400 font-mono text-xs">
                      {opening.games ?? (opening as any).count ?? 0}
                    </td>
                    <td className="py-2.5 pr-2">
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-2 text-xs font-mono">
                          <span className="text-emerald-400 font-semibold">{winPct}% W</span>
                          <span className="text-slate-500">/</span>
                          <span className="text-slate-400">{drawPct}% D</span>
                          <span className="text-slate-500">/</span>
                          <span className="text-rose-400">{lossPct}% L</span>
                        </div>
                        {/* Outcome Proportional Bar */}
                        <div className="flex w-36 h-1.5 rounded-full overflow-hidden bg-slate-800">
                          <div
                            style={{ width: `${winPct}%` }}
                            className="bg-emerald-500 h-full"
                            title={`Win: ${winPct}%`}
                          />
                          <div
                            style={{ width: `${drawPct}%` }}
                            className="bg-slate-500 h-full"
                            title={`Draw: ${drawPct}%`}
                          />
                          <div
                            style={{ width: `${lossPct}%` }}
                            className="bg-rose-500 h-full"
                            title={`Loss: ${lossPct}%`}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

