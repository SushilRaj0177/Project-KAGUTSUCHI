"use client";

// RGB-split "corrupted signal" text -- wraps children in two
// chromatically-offset duplicate layers (cyan + magenta) behind the
// real text, static by default with a slow occasional flicker. This
// is the single most concrete "dystopian/futuristic" signal the first
// two design passes were missing entirely -- everything read as clean
// and undamaged.
export function Glitch({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`glitch-text relative inline-block ${className}`}>
      <span aria-hidden="true" className="glitch-layer glitch-cyan">
        {children}
      </span>
      <span aria-hidden="true" className="glitch-layer glitch-magenta">
        {children}
      </span>
      <span className="relative">{children}</span>
    </span>
  );
}
