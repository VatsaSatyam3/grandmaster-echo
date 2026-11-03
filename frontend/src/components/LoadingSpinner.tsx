"use client";

import React, { useEffect, useState } from "react";
import { Crown } from "lucide-react";

interface LoadingSpinnerProps {
  username?: string;
}

const STEPS = [
  "Connecting to platform API...",
  "Ingesting up to 200 recent games...",
  "Parsing PGNs & extracting ECO repertoire...",
  "Running Stockfish 16 static engine evaluations...",
  "Computing ACPL and phase blunder distribution...",
  "Synthesizing tactical profile via LangGraph agents...",
  "Building playable clone bot parameters...",
];

export default function LoadingSpinner({ username }: LoadingSpinnerProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % STEPS.length);
    }, 2400);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center animate-fade-in">
      <div className="relative mb-6 flex h-20 w-20 items-center justify-center">
        {/* Pulsing glow ring */}
        <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
        <div className="absolute inset-0 rounded-full border-2 border-primary/40 border-t-primary animate-spin" />
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 border border-slate-700/60 shadow-xl">
          <Crown className="h-7 w-7 text-primary animate-pulse" />
        </div>
      </div>

      <h3 className="text-xl font-bold text-white mb-2">
        {username ? `Analyzing ${username}'s Chess Soul` : "Profiling Player"}
      </h3>
      
      <p className="text-sm text-slate-400 max-w-md h-6 transition-all duration-300">
        {STEPS[currentStepIndex]}
      </p>

      {/* Progress dots */}
      <div className="flex gap-1.5 mt-5">
        {STEPS.map((_, i) => (
          <span
            key={i}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              i === currentStepIndex
                ? "w-6 bg-primary"
                : i < currentStepIndex
                ? "w-2 bg-primary/50"
                : "w-2 bg-slate-800"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

