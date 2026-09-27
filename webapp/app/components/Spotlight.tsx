"use client";

import { useReducedMotion } from "motion/react";
import { useEffect, useRef } from "react";

/**
 * A radial glow that tracks the pointer across its parent section. The
 * listener is attached to the parent element itself (pointermove bubbles),
 * not a full-coverage overlay div - so there's nothing sitting in front of
 * the section's real content that could ever intercept a click. Disabled
 * under prefers-reduced-motion and for touch input, where there's no
 * meaningful "hover position" to track.
 */
export default function Spotlight() {
  const markerRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (reduceMotion) return;
    const parent = markerRef.current?.parentElement;
    if (!parent) return;

    function handleMove(e: PointerEvent) {
      if (e.pointerType === "touch") return;
      const rect = parent!.getBoundingClientRect();
      parent!.style.setProperty("--spot-x", `${e.clientX - rect.left}px`);
      parent!.style.setProperty("--spot-y", `${e.clientY - rect.top}px`);
    }

    parent.addEventListener("pointermove", handleMove);
    return () => parent.removeEventListener("pointermove", handleMove);
  }, [reduceMotion]);

  return <div ref={markerRef} className="spotlight-layer" aria-hidden="true" />;
}
