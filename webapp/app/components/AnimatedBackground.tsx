"use client";

import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";

/**
 * A fixed, decorative backdrop: two soft blurred blobs that drift slowly
 * (CSS keyframes - cheap, GPU-composited, and trivially paused via
 * prefers-reduced-motion) plus a faint dot-grid that parallaxes gently
 * against scroll position. Pointer-events are disabled throughout so it
 * never interferes with the real content sitting above it, and it's
 * aria-hidden since it carries no information.
 */
export default function AnimatedBackground() {
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const gridY = useTransform(scrollYProgress, [0, 1], [0, reduceMotion ? 0 : -120]);

  return (
    <div className="bg-scene" aria-hidden="true">
      <div className="bg-blob bg-blob-a" />
      <div className="bg-blob bg-blob-b" />
      <motion.div className="bg-grid" style={{ y: gridY }} />
    </div>
  );
}
