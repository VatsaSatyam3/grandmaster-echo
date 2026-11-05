"use client";

import React from "react";
import { CoachingStep } from "@/lib/types";

interface CoachingPlanProps {
  steps?: CoachingStep[];
  priorities?: string[];
}

export default function CoachingPlan({
  steps = [],
  priorities = [],
}: CoachingPlanProps) {
  const normalizedSteps: CoachingStep[] =
    steps.length > 0
      ? steps
      : priorities.map((priority, index) => ({
          step: index + 1,
          title: `FOCUS_PHASE_${index + 1}`,
          description: priority,
        }));

  if (normalizedSteps.length === 0) {
    return (
      <p className="font-mono text-[11px] text-term-faint">
        // no coaching roadmap generated
      </p>
    );
  }

  return (
    <ol className="border-t border-term-line">
      {normalizedSteps.map((item) => (
        <li
          key={item.step}
          className="flex items-start gap-3 border-b border-term-line px-1 py-3 last:border-b-0"
        >
          <span className="mt-px shrink-0 border border-term-line px-1.5 py-0.5 font-mono text-[10px] text-term-green">
            {String(item.step).padStart(2, "0")}
          </span>
          <div>
            <h4 className="font-mono text-[11px] tracking-wide text-term-text">
              {item.title.toUpperCase()}
            </h4>
            <p className="mt-1 text-[12.5px] leading-5 text-term-muted">
              {item.description}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
