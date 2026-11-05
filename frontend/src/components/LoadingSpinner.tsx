"use client";

import React, { useEffect, useState } from "react";
import { StreamStage } from "@/lib/types";

interface LoadingSpinnerProps {
  username?: string;
  stage?: StreamStage | null;
}

const STEPS: { stage: StreamStage; label: string }[] = [
  { stage: "ingesting", label: "FETCH GAMES" },
  { stage: "parsing", label: "PARSE PGN / ECO" },
  { stage: "engine", label: "STOCKFISH EVAL" },
  { stage: "rag_indexing", label: "EMBED → QDRANT" },
  { stage: "rag_retrieval", label: "SEMANTIC RETRIEVAL" },
  { stage: "agents", label: "LANGGRAPH AGENTS" },
  { stage: "guardrails", label: "GUARDRAIL CHECK" },
  { stage: "evals", label: "SCORE REPORT" },
];

const BAR_WIDTH = 28;

export default function LoadingSpinner({ username, stage }: LoadingSpinnerProps) {
  const [fallbackIndex, setFallbackIndex] = useState(0);

  useEffect(() => {
    if (stage) return;
    const interval = setInterval(() => {
      setFallbackIndex((prev) => Math.min(prev + 1, STEPS.length - 1));
    }, 2200);
    return () => clearInterval(interval);
  }, [stage]);

  const activeIndex = stage
    ? Math.max(
        0,
        STEPS.findIndex((step) => step.stage === stage)
      )
    : fallbackIndex;

  const progress = Math.round(((activeIndex + 1) / STEPS.length) * 100);
  const filled = Math.round((progress / 100) * BAR_WIDTH);

  return (
    <div className="w-full max-w-lg animate-fade-up px-4">
      <div className="border border-term-line bg-term-panel">
        <div className="panel-bar flex items-center justify-between px-3 py-2 font-mono text-[10px] tracking-wider">
          <div className="flex items-center gap-2 text-term-muted">
            <span className="text-term-green">●</span>
            <span>GME://BOOT</span>
          </div>
          <span className="text-term-faint">RUNNING</span>
        </div>

        <div className="p-4 font-mono text-[11px]">
          <div className="text-term-muted">
            <span className="text-term-green">$</span> gme analyze --player{" "}
            <span className="text-term-text">{username || "—"}</span>
          </div>

          <div className="mt-3 space-y-1.5">
            {STEPS.map((step, index) => {
              const done = index < activeIndex;
              const active = index === activeIndex;
              return (
                <div key={step.stage} className="flex items-center gap-2">
                  <span
                    className={
                      done
                        ? "text-term-green"
                        : active
                        ? "text-term-amber"
                        : "text-term-faint"
                    }
                  >
                    {done ? "[ OK ]" : active ? "[ >> ]" : "[ -- ]"}
                  </span>
                  <span
                    className={
                      active
                        ? "text-term-text"
                        : done
                        ? "text-term-muted"
                        : "text-term-faint"
                    }
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-4 flex items-center gap-3 text-[11px]">
            <span className="text-term-green">
              {"█".repeat(filled)}
              <span className="text-term-line-bright">
                {"░".repeat(BAR_WIDTH - filled)}
              </span>
            </span>
            <span className="text-term-muted">{progress}%</span>
          </div>

          <div className="mt-3 border-t border-term-line pt-2 text-[9px] leading-4 text-term-faint">
            // output is grounded in Stockfish evaluations and retrieved games
          </div>
        </div>
      </div>
    </div>
  );
}
