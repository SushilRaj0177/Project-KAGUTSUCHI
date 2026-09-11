// Slow, continuously drifting scan-light band -- see the `.scan-sweep`
// CSS in globals.css. Pure CSS (no JS/canvas cost), but it's real,
// perpetual motion, not a static gradient -- the concrete difference
// between "looks like an instrument panel" and "is a live scanning
// system."
export function Sweep({ className = "" }: { className?: string }) {
  return <div className={`scan-sweep ${className}`} aria-hidden="true" />;
}
