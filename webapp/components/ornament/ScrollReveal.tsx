"use client";

import { useInView } from "./useInView";

// Reveals its children on scroll (a clip-path wipe + fade, matching the
// instrument-panel language better than a generic fade-up) instead of
// having every section fully rendered and static the instant the page
// loads.
//
// The observed element and the clipped element are deliberately NOT
// the same node. A real bug found while testing this: applying
// `clip-path: inset(0 0 100% 0)` (the pre-reveal "wipe" state) directly
// to the element passed to IntersectionObserver makes Chromium compute
// its visible area as zero, so `isIntersecting` never becomes true --
// the element needs to be seen to reveal itself, but the reveal style
// hides it from being seen. Confirmed by testing the same element with
// and without the clip-path against a raw IntersectionObserver
// (isIntersecting stayed false forever with it, true immediately
// without it). Fixed by observing a plain, never-clipped outer
// wrapper, and applying the clip-path/opacity transition to an inner
// child instead.
export function ScrollReveal({
  children,
  className = "",
  delayMs = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delayMs?: number;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  return (
    <div ref={ref} className={className}>
      <div className={`reveal ${inView ? "reveal-in" : ""}`} style={{ transitionDelay: inView ? `${delayMs}ms` : "0ms" }}>
        {children}
      </div>
    </div>
  );
}
