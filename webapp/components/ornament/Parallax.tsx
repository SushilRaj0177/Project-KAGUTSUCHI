"use client";

import { useEffect, useRef } from "react";

// Mouse- and scroll-driven depth for a layer -- `depth` controls how far
// it shifts relative to pointer movement (px), `scrollSpeed` controls
// how much it drifts opposite the scroll position (a fraction, e.g.
// 0.15). Two elements with different depth values moving at different
// rates as you move the mouse or scroll is what makes a HUD read as a
// physical 3D instrument rather than a flat printed panel.
export function Parallax({
  children,
  depth = 16,
  scrollSpeed = 0,
  className = "",
}: {
  children: React.ReactNode;
  depth?: number;
  scrollSpeed?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let mouseX = 0;
    let mouseY = 0;
    let frame: number;

    function onMove(e: MouseEvent) {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = (e.clientY / window.innerHeight) * 2 - 1;
    }

    function tick() {
      if (ref.current) {
        const scrollShift = scrollSpeed ? window.scrollY * scrollSpeed : 0;
        ref.current.style.transform = `translate3d(${mouseX * depth}px, ${mouseY * depth - scrollShift}px, 0)`;
      }
      frame = requestAnimationFrame(tick);
    }

    window.addEventListener("mousemove", onMove, { passive: true });
    frame = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(frame);
    };
  }, [depth, scrollSpeed]);

  return (
    <div ref={ref} className={className} style={{ willChange: "transform" }}>
      {children}
    </div>
  );
}
