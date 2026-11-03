"use client";

import React from "react";
import { CoachingStep } from "@/lib/types";
import { Target, Compass, ChevronRight } from "lucide-react";

interface CoachingPlanProps {
  steps?: CoachingStep[];
  priorities?: string[];
}

export default function CoachingPlan({ steps = [], priorities = [] }: CoachingPlanProps) {
  // If steps array is empty, generate from priorities
  const normalizedSteps: CoachingStep[] =
    steps.length > 0
      ? steps
      : priorities.map((p, idx) => ({
          step: idx + 1,
          title: `Focus Phase ${idx + 1}`,
          description: p,
        }));

  if (normalizedSteps.length === 0) {
    return (
      <div className="p-4 text-xs text-slate-500 italic">
        No tailored coaching roadmap generated yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {normalizedSteps.map((item) => (
        <div
          key={item.step}
          className="flex items-start gap-3.5 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all group"
        >
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/20 text-primary-300 font-bold text-xs ring-1 ring-primary/30">
            {item.step}
          </div>
          <div className="flex-1">
            <h4 className="text-xs font-semibold text-white group-hover:text-primary-300 transition-colors flex items-center gap-1.5">
              <span>{item.title}</span>
              <ChevronRight className="w-3 h-3 text-slate-600 group-hover:text-primary-400 group-hover:translate-x-0.5 transition-all" />
            </h4>
            <p className="mt-1 text-xs text-slate-400 leading-relaxed">
              {item.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

