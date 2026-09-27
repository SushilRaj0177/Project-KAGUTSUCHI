"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ElementType } from "react";

type WordRevealProps = {
  text: string;
  as?: ElementType;
  className?: string;
  /** Seconds before the first word starts. */
  delay?: number;
  /** Seconds between each word's start. */
  stagger?: number;
};

/**
 * Splits `text` on whitespace and reveals each word with a staggered
 * fade + rise, triggered once when the element scrolls into view.
 *
 * IMPORTANT: whileInView is set on the outer, untransformed masking span,
 * never on the inner span that actually carries the y-offset. Putting
 * whileInView directly on an element whose OWN initial state transforms
 * it outside its own overflow:hidden ancestor's clip box creates a
 * deadlock: IntersectionObserver computes intersection against the
 * clipped (i.e. invisible) box, so it reports "not intersecting" forever,
 * and the animation that would reveal it can then never start. Observing
 * the stable outer wrapper instead, and driving the inner transform via
 * variants (which Framer Motion propagates to children automatically),
 * sidesteps this entirely - a real bug hit and fixed during development,
 * not a stylistic choice.
 *
 * Words themselves stay intact (no letter-splitting) so line-wrapping and
 * screen readers both keep behaving normally - the DOM's accessible text
 * content is the plain, unsplit string via aria-label, with the animated
 * spans hidden from assistive tech.
 */
export default function WordReveal({ text, as = "span", className, delay = 0, stagger = 0.045 }: WordRevealProps) {
  const reduceMotion = useReducedMotion();
  const Tag = motion[as as "span"];
  const words = text.split(" ");

  if (reduceMotion) {
    return (
      <Tag className={className} aria-label={text}>
        {text}
      </Tag>
    );
  }

  return (
    <Tag className={className} aria-label={text}>
      {words.map((word, i) => (
        <motion.span
          key={i}
          style={{ display: "inline-block", overflow: "hidden", verticalAlign: "top" }}
          aria-hidden="true"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0 }}
        >
          <motion.span
            style={{ display: "inline-block" }}
            variants={{ hidden: { y: "110%", opacity: 0 }, visible: { y: "0%", opacity: 1 } }}
            transition={{
              duration: 0.65,
              delay: delay + i * stagger,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            {word}
            {i < words.length - 1 ? " " : ""}
          </motion.span>
        </motion.span>
      ))}
    </Tag>
  );
}
