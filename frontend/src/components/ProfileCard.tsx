"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface ProfileCardProps {
  title: string;
  kicker?: string;
  className?: string;
  children: React.ReactNode;
}

/**
 * Terminal panel: a 1px border, a compact header bar with a prompt marker and
 * an optional right-aligned kicker. No shadows, gradients, or rounded cards.
 */
export default function ProfileCard({
  title,
  kicker,
  className,
  children,
}: ProfileCardProps) {
  return (
    <section className={cn("border border-term-line bg-term-panel", className)}>
      <div className="panel-bar flex items-center justify-between gap-3 px-3 py-2">
        <div className="flex items-center gap-2 font-mono text-[10px] tracking-wider">
          <span className="text-term-green">▸</span>
          <h3 className="text-term-text">{title}</h3>
        </div>
        {kicker && (
          <span className="font-mono text-[9px] tracking-wider text-term-faint">
            {kicker}
          </span>
        )}
      </div>
      <div className="p-4">{children}</div>
    </section>
  );
}
