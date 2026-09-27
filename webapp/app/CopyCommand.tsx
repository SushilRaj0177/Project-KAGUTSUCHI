"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { spawnRipple } from "./components/ripple";

export default function CopyCommand({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      // clipboard API unavailable - the visible command text is still selectable
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  }

  return (
    <motion.div
      className="cmd"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
    >
      {command}
      <motion.button
        className="ripple-host"
        onPointerDown={spawnRipple}
        onClick={handleCopy}
        whileHover={{ scale: 1.04 }}
        whileTap={{ scale: 0.92 }}
        animate={copied ? { backgroundColor: "var(--accent)", color: "var(--accent-ink)" } : {}}
        transition={{ duration: 0.2 }}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={copied ? "copied" : "copy"}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            style={{ display: "inline-block" }}
          >
            {copied ? "Copied ✓" : "Copy"}
          </motion.span>
        </AnimatePresence>
      </motion.button>
    </motion.div>
  );
}
