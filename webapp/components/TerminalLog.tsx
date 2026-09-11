"use client";

import { useEffect, useState } from "react";

const EVENTS = [
  "[SCAN]   app/auth/session.py — parsing AST",
  "[SCAN]   app/db/query_builder.py — 3 candidates found",
  "[AI]     reviewing sensitive_op: sql_query",
  "[ATTACK] payload dispatched to sandbox (network disabled)",
  "[SANDBOX] container exit 0, filesystem diff captured",
  "[VERIFY] marker created — exploit confirmed",
  "[FIX]    proposing parameterized query",
  "[REPLAY] identical payload vs. patched code",
  "[VERIFY] marker absent — fix holds",
  "[VERDICT] VERIFIED_FIXED",
  "[SCAN]   app/api/upload.py — checking filesystem ops",
  "[AI]     no new vulnerability class detected",
];

// A slowly-typing log feed, standing in for "this is a live running
// system" -- appends real lines on an interval rather than a static
// block of pre-written text.
export function TerminalLog({ className = "" }: { className?: string }) {
  const [lines, setLines] = useState<string[]>([EVENTS[0]]);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let i = 1;
    const id = setInterval(() => {
      setLines((prev) => {
        const next = [...prev, EVENTS[i % EVENTS.length]];
        i += 1;
        return next.slice(-6);
      });
    }, 1400);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={`font-mono text-[11px] leading-relaxed ${className}`}>
      {lines.map((line, idx) => (
        <div key={idx} className="whitespace-nowrap text-slate-400/80" style={{ opacity: 0.4 + (idx / lines.length) * 0.6 }}>
          {line}
        </div>
      ))}
      <div className="mt-0.5 inline-block h-3 w-1.5 animate-pulse bg-slate-300/70" />
    </div>
  );
}
