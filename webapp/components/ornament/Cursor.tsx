"use client";

import { useEffect, useRef } from "react";

// Custom crosshair cursor -- replaces the system pointer with a small
// ring + crosshair that trails slightly behind the real pointer,
// consistent with the instrument-panel language (see Crosshair.tsx)
// instead of a generic dot. This, a moving scan sweep (Sweep.tsx), and
// real animated glitch are what separate an interactive system from a
// static poster -- a site with no cursor feedback and no motion reads
// as a document no matter how detailed its imagery is.
//
// Only takes over on devices with a real mouse (matchMedia pointer:
// fine) and respects prefers-reduced-motion by skipping the trailing
// lag. Never intercepts clicks -- pointer-events: none throughout.
export function Cursor() {
  const ringRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!window.matchMedia("(pointer: fine)").matches) return;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    document.documentElement.classList.add("custom-cursor-active");

    let ringX = window.innerWidth / 2;
    let ringY = window.innerHeight / 2;
    let targetX = ringX;
    let targetY = ringY;

    function onMove(e: MouseEvent) {
      targetX = e.clientX;
      targetY = e.clientY;
      if (dotRef.current) {
        dotRef.current.style.transform = `translate(${targetX}px, ${targetY}px)`;
      }
      if (reduceMotion && ringRef.current) {
        ringRef.current.style.transform = `translate(${targetX}px, ${targetY}px)`;
      }
    }

    let frame: number;
    function tick() {
      ringX += (targetX - ringX) * 0.18;
      ringY += (targetY - ringY) * 0.18;
      if (ringRef.current) {
        ringRef.current.style.transform = `translate(${ringX}px, ${ringY}px)`;
      }
      frame = requestAnimationFrame(tick);
    }

    window.addEventListener("mousemove", onMove);
    if (!reduceMotion) frame = requestAnimationFrame(tick);

    return () => {
      document.documentElement.classList.remove("custom-cursor-active");
      window.removeEventListener("mousemove", onMove);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <>
      <div ref={dotRef} className="cursor-dot" aria-hidden="true" />
      <div ref={ringRef} className="cursor-ring" aria-hidden="true">
        <span className="cursor-tick cursor-tick-t" />
        <span className="cursor-tick cursor-tick-r" />
        <span className="cursor-tick cursor-tick-b" />
        <span className="cursor-tick cursor-tick-l" />
      </div>
    </>
  );
}
