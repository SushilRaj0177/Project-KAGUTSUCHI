"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";
import type { ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  /** Stagger delay in seconds, for revealing a list of Reveal siblings in sequence. */
  delay?: number;
  /** Direction the content travels in from. */
  from?: "up" | "down" | "left" | "right" | "none";
  /** Render as a different element than a plain div (e.g. "section", "li"). */
  as?: "div" | "section" | "li";
  className?: string;
};

const DISTANCE = 28;

function variantsFor(from: RevealProps["from"]): Variants {
  const offset =
    from === "up"
      ? { y: DISTANCE }
      : from === "down"
        ? { y: -DISTANCE }
        : from === "left"
          ? { x: DISTANCE }
          : from === "right"
            ? { x: -DISTANCE }
            : {};
  return {
    hidden: { opacity: 0, ...offset },
    visible: { opacity: 1, x: 0, y: 0 },
  };
}

/**
 * Fades + slides children into place the first time they scroll into view.
 * Respects prefers-reduced-motion by skipping the motion entirely (still
 * fades in, since opacity alone doesn't trigger vestibular discomfort).
 */
export default function Reveal({ children, delay = 0, from = "up", as = "div", className }: RevealProps) {
  const reduceMotion = useReducedMotion();
  const MotionTag = motion[as];

  return (
    <MotionTag
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-80px" }}
      variants={reduceMotion ? { hidden: { opacity: 0 }, visible: { opacity: 1 } } : variantsFor(from)}
      transition={{ duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </MotionTag>
  );
}
