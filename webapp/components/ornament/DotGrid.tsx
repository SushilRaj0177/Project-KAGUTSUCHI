// The small dotted-grid glyph from the reference boards (⁘-like cluster).
// Purely decorative texture, used sparingly next to a heading or in a
// panel corner -- never as a repeating page-wide pattern.
export function DotGrid({ cols = 3, rows = 3, gap = 4, className = "" }: { cols?: number; rows?: number; gap?: number; className?: string }) {
  return (
    <div
      className={`inline-grid ${className}`}
      style={{ gridTemplateColumns: `repeat(${cols}, 2px)`, gap }}
      aria-hidden="true"
    >
      {Array.from({ length: cols * rows }).map((_, i) => (
        <span key={i} className="h-[2px] w-[2px] rounded-full bg-current" />
      ))}
    </div>
  );
}
