"use client";

import { useEffect, useState } from "react";

// A small readout that visibly ticks upward on an interval -- one more
// concrete "this is a live system, not a printed page" signal. Starts
// from `from` and increments by a random small step so it never looks
// like a suspiciously round fake counter.
export function LiveCounter({ from, suffix = "", className = "" }: { from: number; suffix?: string; className?: string }) {
  const [value, setValue] = useState(from);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => {
      setValue((v) => v + Math.floor(Math.random() * 3) + 1);
    }, 2200);
    return () => clearInterval(id);
  }, []);

  return (
    <span className={`font-mono-tech tabular-nums ${className}`}>
      {value.toLocaleString()}
      {suffix}
    </span>
  );
}
