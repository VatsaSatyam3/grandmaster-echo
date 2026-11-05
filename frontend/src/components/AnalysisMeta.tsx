"use client";

import React from "react";
import { EvalMetrics, GuardrailResult, RAGCitation } from "@/lib/types";

interface AnalysisMetaProps {
  citations?: RAGCitation[];
  evals?: EvalMetrics;
  guardrails?: GuardrailResult;
  ragEnabled?: boolean;
  pipelineMs?: Record<string, number>;
}

const METRIC_LABELS: { key: keyof EvalMetrics; label: string }[] = [
  { key: "schema_validity", label: "SCHEMA_VALIDITY" },
  { key: "elo_alignment", label: "ELO_ALIGNMENT" },
  { key: "opening_grounding", label: "OPENING_GROUNDING" },
  { key: "citation_coverage", label: "CITATION_COVERAGE" },
  { key: "guardrail_pass", label: "GUARDRAIL_PASS" },
];

const BAR_WIDTH = 12;

function Meter({ value }: { value: number }) {
  const filled = Math.round(Math.max(0, Math.min(1, value)) * BAR_WIDTH);
  return (
    <span className="font-mono text-[10px] leading-none">
      <span className="text-term-green">{"█".repeat(filled)}</span>
      <span className="text-term-line-bright">
        {"░".repeat(BAR_WIDTH - filled)}
      </span>
    </span>
  );
}

export default function AnalysisMeta({
  citations = [],
  evals,
  guardrails,
  ragEnabled,
  pipelineMs,
}: AnalysisMetaProps) {
  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
      <div className="lg:col-span-7">
        <div className="mb-2 flex items-center justify-between font-mono text-[9px] tracking-wider">
          <span className="text-term-faint">RETRIEVED_EVIDENCE</span>
          <span className="text-term-faint">
            {ragEnabled ? "QDRANT / TOP-K" : "FALLBACK INDEX"}
          </span>
        </div>

        {citations.length === 0 ? (
          <p className="border border-term-line px-3 py-4 font-mono text-[10px] text-term-faint">
            // no games retrieved for this run
          </p>
        ) : (
          <ol className="border border-term-line">
            {citations.map((citation) => (
              <li
                key={citation.game_id}
                className="border-b border-term-line/70 px-3 py-2.5 last:border-b-0"
              >
                <div className="flex items-baseline justify-between gap-3">
                  <div className="flex min-w-0 items-baseline gap-2">
                    <span className="shrink-0 font-mono text-[10px] text-term-green">
                      {citation.eco}
                    </span>
                    <span className="truncate text-[12px] text-term-text/85">
                      {citation.opening}
                    </span>
                  </div>
                  <span className="shrink-0 font-mono text-[10px] text-term-muted">
                    {citation.score.toFixed(2)}
                  </span>
                </div>
                <div className="mt-1 font-mono text-[9px] tracking-wide text-term-faint">
                  {citation.played_as.toUpperCase()} · {citation.result.toUpperCase()} ·{" "}
                  {citation.game_id.slice(0, 8).toUpperCase()}
                </div>
                <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-term-muted">
                  {citation.excerpt}
                </p>
              </li>
            ))}
          </ol>
        )}
      </div>

      <div className="lg:col-span-5 lg:border-l lg:border-term-line lg:pl-5">
        <div className="mb-2 font-mono text-[9px] tracking-wider text-term-faint">
          EVALUATION_SCORES
        </div>

        {evals ? (
          <>
            <div className="flex items-baseline gap-3 border border-term-line bg-term-raised px-3 py-2">
              <span className="tnum text-3xl leading-none text-term-green">
                {Math.round(evals.overall * 100)}
              </span>
              <span className="font-mono text-[9px] tracking-wider text-term-faint">
                COMPOSITE / 100
              </span>
            </div>

            <dl className="mt-2 space-y-1.5">
              {METRIC_LABELS.map(({ key, label }) => {
                const value = evals[key] as number;
                return (
                  <div
                    key={key}
                    className="flex items-center justify-between gap-3 font-mono text-[10px]"
                  >
                    <dt className="text-term-muted">{label}</dt>
                    <dd className="flex items-center gap-2">
                      <Meter value={value} />
                      <span className="w-8 text-right text-term-faint">
                        {Math.round(value * 100)}%
                      </span>
                    </dd>
                  </div>
                );
              })}
            </dl>
          </>
        ) : (
          <p className="font-mono text-[10px] text-term-faint">
            // no evaluation bundle
          </p>
        )}

        <div className="mt-4 border-t border-term-line pt-2">
          <div className="flex items-center justify-between font-mono text-[9px] tracking-wider">
            <span className="text-term-faint">GUARDRAILS</span>
            <span
              className={
                guardrails?.passed ? "text-term-green" : "text-term-amber"
              }
            >
              {guardrails?.passed ? "[ PASS ]" : "[ REVIEW ]"}
            </span>
          </div>
          <p className="mt-1.5 font-mono text-[10px] leading-4 text-term-muted">
            {guardrails
              ? `${guardrails.checks_run} deterministic checks vs stockfish`
              : "// no guardrail report"}
          </p>
          {guardrails && guardrails.issues.length > 0 && (
            <ul className="mt-1.5 space-y-1">
              {guardrails.issues.map((issue, index) => (
                <li
                  key={`${issue.rule}-${index}`}
                  className="font-mono text-[9px] leading-4 text-term-muted"
                >
                  <span
                    className={
                      issue.severity === "error"
                        ? "text-term-red"
                        : "text-term-amber"
                    }
                  >
                    [{issue.severity.toUpperCase()}]
                  </span>{" "}
                  {issue.message}
                </li>
              ))}
            </ul>
          )}
        </div>

        {pipelineMs && (
          <div className="mt-3 flex items-center justify-between border-t border-term-line pt-2 font-mono text-[9px] tracking-wider">
            <span className="text-term-faint">PIPELINE_LATENCY</span>
            <span className="text-term-muted">
              {(pipelineMs.total_ms ?? evals?.latency_ms ?? 0).toFixed(0)} MS
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
