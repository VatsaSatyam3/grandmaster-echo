"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck, ZapOff } from "lucide-react";

interface StrengthWeaknessProps {
  strengths: string[];
  weaknesses: string[];
}

export default function StrengthWeakness({
  strengths,
  weaknesses,
}: StrengthWeaknessProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Strengths Column */}
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-4">
        <div className="flex items-center gap-2 mb-3 text-emerald-400 font-semibold text-sm uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4" />
          <span>Calculated Strengths</span>
        </div>
        <ul className="space-y-2.5">
          {strengths.length === 0 ? (
            <li className="text-xs text-slate-500 italic">No specific strengths identified.</li>
          ) : (
            strengths.map((str, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{str}</span>
              </li>
            ))
          )}
        </ul>
      </div>

      {/* Weaknesses Column */}
      <div className="rounded-xl border border-rose-500/20 bg-rose-950/10 p-4">
        <div className="flex items-center gap-2 mb-3 text-rose-400 font-semibold text-sm uppercase tracking-wider">
          <ZapOff className="w-4 h-4" />
          <span>Fatal Vulnerabilities</span>
        </div>
        <ul className="space-y-2.5">
          {weaknesses.length === 0 ? (
            <li className="text-xs text-slate-500 italic">No critical vulnerabilities detected.</li>
          ) : (
            weaknesses.map((weak, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{weak}</span>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

