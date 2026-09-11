// Generative atmosphere piece for hero sections -- built from code
// rather than photographed, standing in for the reference boards'
// glowing-figure-on-light-lines and diagonal-plane compositions (no
// image-generation tool available in this environment; see
// COORDINATION.md). Thin diagonal lines converge toward a soft glow,
// with a scatter of coordinate-style mono readouts along them -- the
// same instrument-panel-meets-elegy feeling, constructed instead of shot.
export function LineField({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 900 900"
      className={className}
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="lf-glow" cx="50%" cy="46%" r="55%">
          <stop offset="0%" stopColor="var(--paper)" stopOpacity="0.16" />
          <stop offset="35%" stopColor="var(--paper)" stopOpacity="0.05" />
          <stop offset="100%" stopColor="var(--paper)" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="lf-line" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--paper)" stopOpacity="0" />
          <stop offset="50%" stopColor="var(--paper)" stopOpacity="0.5" />
          <stop offset="100%" stopColor="var(--paper)" stopOpacity="0" />
        </linearGradient>
        <filter id="lf-blur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.1" />
        </filter>
      </defs>

      <rect width="900" height="900" fill="url(#lf-glow)" />

      {/* converging diagonal lines, echoing the reference's X/hourglass
          light-lines meeting at a single point of presence */}
      {[
        [0, 120, 900, 700],
        [0, 780, 900, 200],
        [0, 420, 900, 460],
        [140, 0, 780, 900],
        [660, 0, 220, 900],
      ].map(([x1, y1, x2, y2], i) => (
        <line
          key={i}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="url(#lf-line)"
          strokeWidth={i === 2 ? 1 : 0.6}
          filter="url(#lf-blur)"
        />
      ))}

      {/* scattered coordinate-style readouts along the field -- kept out
          of the corners (0-15% from any edge), which is where real nav
          and hero content sit when this is used as a full-bleed
          background; a label colliding with real UI reads as a bug,
          not atmosphere. */}
      {[
        [64, 470, "07 . 2"],
        [812, 500, "LV3"],
        [150, 730, "D0"],
        [700, 760, "192°"],
      ].map(([x, y, label], i) => (
        <text
          key={i}
          x={x as number}
          y={y as number}
          fontFamily="var(--font-mono)"
          fontSize="11"
          letterSpacing="1.5"
          fill="var(--steel-500)"
        >
          {label}
        </text>
      ))}
    </svg>
  );
}
