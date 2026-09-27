"use client";

import { motion, useScroll, useSpring } from "motion/react";

/**
 * A thin accent-colored bar pinned under the header that fills as the user
 * scrolls the page. useSpring smooths the raw scroll fraction so it reads
 * as fluid motion rather than a value snapping every frame.
 */
export default function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 300, damping: 40, mass: 0.2 });

  return <motion.div className="scroll-progress" style={{ scaleX }} aria-hidden="true" />;
}
