// A small "+" instrument mark -- the recurring precision-point motif
// from the reference boards (used to mark coordinates, corners, and
// points of interest on a panel). Deliberately tiny and thin-stroked;
// it should read as etched detail, not an icon.
export function Crosshair({ size = 10, className = "" }: { size?: number; className?: string }) {
  const half = size / 2;
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      aria-hidden="true"
    >
      <line x1={half} y1={0} x2={half} y2={size} stroke="currentColor" strokeWidth={1} />
      <line x1={0} y1={half} x2={size} y2={half} stroke="currentColor" strokeWidth={1} />
    </svg>
  );
}
