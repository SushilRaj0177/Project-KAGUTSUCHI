"use client";

import { motion } from "motion/react";
import type { ElementType, ReactNode } from "react";

type HoverableProps = {
  tag?: ElementType;
  className?: string;
  children: ReactNode;
};

/** A stat/badge/card that lifts a couple pixels on hover - subtle, no scale/bounce. */
export function HoverStat({ tag = "div", className, children }: HoverableProps) {
  const Tag = motion[tag as "div"];
  return (
    <Tag className={className} whileHover={{ y: -2 }} transition={{ duration: 0.18, ease: "easeOut" }}>
      {children}
    </Tag>
  );
}

/** A table row / pipeline stage - hover feedback is plain CSS (see globals.css), no JS motion needed. */
export function HoverRow({ tag = "tr", className, children }: HoverableProps) {
  const Tag = tag as "tr";
  return <Tag className={className}>{children}</Tag>;
}
