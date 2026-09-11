// A hairline divider with small perpendicular tick marks -- the ruler
// motif that runs across the reference boards, often carrying a couple
// of coordinate-style labels. Horizontal by default.
export function TickRuler({
  ticks = 12,
  labelLeft,
  labelRight,
  className = "",
}: {
  ticks?: number;
  labelLeft?: string;
  labelRight?: string;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {labelLeft && (
        <span className="font-mono-tech shrink-0 text-[10px] text-[var(--steel-500)] uppercase">{labelLeft}</span>
      )}
      <div className="relative h-2 flex-1">
        <div className="absolute top-1/2 right-0 left-0 h-px bg-[var(--line)]" />
        <div className="absolute inset-0 flex items-center justify-between">
          {Array.from({ length: ticks }).map((_, i) => (
            <span key={i} className="h-1.5 w-px bg-[var(--line-strong)]" />
          ))}
        </div>
      </div>
      {labelRight && (
        <span className="font-mono-tech shrink-0 text-[10px] text-[var(--steel-500)] uppercase">{labelRight}</span>
      )}
    </div>
  );
}
