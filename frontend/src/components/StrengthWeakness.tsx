"use client";

import React from "react";

interface StrengthWeaknessProps {
  strengths: string[];
  weaknesses: string[];
}

function ItemList({
  items,
  marker,
  markerClass,
  empty,
}: {
  items: string[];
  marker: string;
  markerClass: string;
  empty: string;
}) {
  return (
    <ul className="mt-3 space-y-2">
      {items.length === 0 ? (
        <li className="font-mono text-[11px] text-term-faint">{empty}</li>
      ) : (
        items.map((item, index) => (
          <li
            key={index}
            className="flex items-start gap-2.5 text-[12.5px] leading-5 text-term-text/80"
          >
            <span
              aria-hidden
              className={`mt-px shrink-0 font-mono text-[11px] ${markerClass}`}
            >
              {marker}
            </span>
            <span>{item}</span>
          </li>
        ))
      )}
    </ul>
  );
}

export default function StrengthWeakness({
  strengths,
  weaknesses,
}: StrengthWeaknessProps) {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
      <div>
        <p className="font-mono text-[10px] tracking-wider text-term-green">
          [+] STRENGTHS
        </p>
        <ItemList
          items={strengths}
          marker="+"
          markerClass="text-term-green"
          empty="// none identified"
        />
      </div>
      <div className="md:border-l md:border-term-line md:pl-5">
        <p className="font-mono text-[10px] tracking-wider text-term-red">
          [−] FAILURES
        </p>
        <ItemList
          items={weaknesses}
          marker="−"
          markerClass="text-term-red"
          empty="// none detected"
        />
      </div>
    </div>
  );
}
