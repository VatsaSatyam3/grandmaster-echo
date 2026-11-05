"use client";

import React, { useState } from "react";
import { OpeningStats } from "@/lib/types";
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
  const [expanded, setExpanded] = useState(false);

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
    const gamesA = a.games ?? a.count ?? 0;
    const gamesB = b.games ?? b.count ?? 0;
    return gamesB - gamesA;
  });

  const ROW_LIMIT = 12;
  const visibleOpenings = expanded
    ? sortedOpenings
    : sortedOpenings.slice(0, ROW_LIMIT);
  const hiddenCount = sortedOpenings.length - visibleOpenings.length;

  const selectTab = (tab: "white" | "black") => {
    setActiveTab(tab);
    setExpanded(false);
  };

  const toggleSort = () => {
    setSortBy((prev) => (prev === "games" ? "win_rate" : "games"));
    setExpanded(false);
  };

  const tabClass = (active: boolean) =>
    cn(
      "px-2 py-1 font-mono text-[10px] tracking-wider transition-colors",
      active
        ? "bg-term-raised text-term-green"
        : "text-term-faint hover:text-term-text"
    );

  return (
    <div className="w-full">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1 border border-term-line bg-term-panel">
          <button
            onClick={() => selectTab("white")}
            className={tabClass(activeTab === "white")}
          >
            [WHITE {whiteOpenings.length || generalOpenings.length}]
          </button>
          <button
            onClick={() => selectTab("black")}
            className={tabClass(activeTab === "black")}
          >
            [BLACK {blackOpenings.length || generalOpenings.length}]
          </button>
        </div>

        <button
          onClick={toggleSort}
          className="border border-term-line px-2 py-1 font-mono text-[10px] tracking-wider text-term-muted transition-colors hover:border-term-line-bright hover:text-term-text"
        >
          SORT: {sortBy === "games" ? "GAMES" : "WIN%"}
        </button>
      </div>

      {sortedOpenings.length === 0 ? (
        <p className="border border-term-line px-3 py-6 text-center font-mono text-[11px] text-term-faint">
          // no opening data for this side
        </p>
      ) : (
        <div className="overflow-x-auto border border-term-line">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-term-line bg-term-raised">
                {["ECO", "OPENING", "G", "W / D / L"].map((header) => (
                  <th
                    key={header}
                    className={cn(
                      "px-3 py-2 font-mono text-[9px] font-medium tracking-wider text-term-faint",
                      header === "G" && "text-center",
                      header === "W / D / L" && "text-right"
                    )}
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleOpenings.map((opening) => {
                const winPct = Math.round((opening.win_rate || 0) * 100);
                const drawPct = Math.round((opening.draw_rate || 0) * 100);
                const lossPct = Math.max(0, 100 - winPct - drawPct);

                return (
                  <tr
                    key={opening.eco + opening.name}
                    className="border-b border-term-line/70 transition-colors last:border-b-0 hover:bg-term-raised"
                  >
                    <td className="whitespace-nowrap px-3 py-2 font-mono text-[10px] text-term-green">
                      {opening.eco || "N/A"}
                    </td>
                    <td className="max-w-[22rem] truncate px-3 py-2 text-[12px] text-term-text/85">
                      {opening.name || "Custom opening"}
                    </td>
                    <td className="px-3 py-2 text-center font-mono text-[10px] text-term-muted">
                      {opening.games ?? opening.count ?? 0}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-1 font-mono text-[10px]">
                          <span className="text-term-green">{winPct}</span>
                          <span className="text-term-faint">/</span>
                          <span className="text-term-muted">{drawPct}</span>
                          <span className="text-term-faint">/</span>
                          <span className="text-term-red">{lossPct}</span>
                        </div>
                        <div className="flex h-1 w-28 overflow-hidden bg-term-line">
                          <div
                            style={{ width: `${winPct}%` }}
                            className="h-full bg-term-green"
                          />
                          <div
                            style={{ width: `${drawPct}%` }}
                            className="h-full bg-term-faint"
                          />
                          <div
                            style={{ width: `${lossPct}%` }}
                            className="h-full bg-term-red"
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

      {sortedOpenings.length > ROW_LIMIT && (
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="mt-2 flex w-full items-center justify-between border border-term-line px-3 py-1.5 font-mono text-[10px] tracking-wider text-term-muted transition-colors hover:border-term-line-bright hover:text-term-text"
          aria-expanded={expanded}
        >
          <span>
            {expanded
              ? "[ COLLAPSE ]"
              : `[ SHOW ALL +${hiddenCount} ]`}
          </span>
          <span className="text-term-faint">
            {visibleOpenings.length} / {sortedOpenings.length} ROWS
          </span>
        </button>
      )}
    </div>
  );
}
