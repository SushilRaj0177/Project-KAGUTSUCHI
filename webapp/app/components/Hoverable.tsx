"use client";

import { motion } from "motion/react";
import type { ElementType, ReactNode } from "react";

type HoverableProps = {
  tag?: ElementType;
  className?: string;
  children: ReactNode;
};

/** A stat/badge that lifts and scales slightly on hover, settles with a spring on release. */
export function HoverStat({ tag = "div", className, children }: HoverableProps) {
  const Tag = motion[tag as "div"];
  return (
    <Tag
      className={className}
      whileHover={{ y: -4, scale: 1.04 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: "spring", stiffness: 420, damping: 24 }}
    >
      {children}
    </Tag>
  );
}

/** A table row / pipeline stage that highlights and nudges right on hover. */
export function HoverRow({ tag = "tr", className, children }: HoverableProps) {
  const Tag = motion[tag as "tr"];
  return (
    <Tag
      className={className}
      whileHover={{ x: 4, backgroundColor: "var(--surface)" }}
      transition={{ type: "spring", stiffness: 500, damping: 32 }}
    >
      {children}
    </Tag>
  );
}
