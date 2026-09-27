"use client";

import { useState } from "react";

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
    <div className="cmd">
      {command}
      <button onClick={handleCopy}>{copied ? "Copied" : "Copy"}</button>
    </div>
  );
}
