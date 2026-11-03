"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface ProfileCardProps {
  title: string;
  icon?: React.ReactNode;
  borderColor?: string;
  className?: string;
  children: React.ReactNode;
}

export default function ProfileCard({
  title,
  icon,
  borderColor = "border-primary/40",
  className,
  children,
}: ProfileCardProps) {
  return (
    <div
      className={cn(
        "glass group relative overflow-hidden rounded-2xl transition-all duration-300 hover:border-slate-600/30",
        className
      )}
    >
      {/* Colored top border */}
      <div
        className={cn(
          "absolute inset-x-0 top-0 h-[2px] rounded-full",
          borderColor.replace("border-", "bg-")
        )}
      />

      <div className="p-5">
        {/* Header */}
        <div className="mb-4 flex items-center gap-2.5">
          {icon && (
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700/50 text-slate-300 transition-colors group-hover:text-white">
              {icon}
            </div>
          )}
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </h3>
        </div>

        {/* Content */}
        {children}
      </div>
    </div>
  );
}
