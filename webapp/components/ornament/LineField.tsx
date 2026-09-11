// Generative atmosphere piece for hero sections -- built from code
// rather than photographed, standing in for the reference boards'
// glowing-figure-on-light-lines and diagonal-plane compositions (no
// image-generation tool available in this environment; see
// COORDINATION.md). Lines converge toward a soft glow with a genuine
// blurred bloom pass (not just a thin flat stroke), plus a scatter of
// coordinate-style mono readouts -- the same instrument-panel-meets-
// elegy feeling, constructed instead of shot.
const VARIANTS = {
  a: {
    lines: [
      [0, 120, 900, 700],
      [0, 780, 900, 200],
      [0, 420, 900, 460],
      [140, 0, 780, 900],
      [660, 0, 220, 900],
    ],
    labels: [
      [64, 470, "07 . 2"],
      [812, 500, "LV3"],
      [150, 730, "D0"],
      [700, 760, "192°"],
    ],
  },
  b: {
    lines: [
      [0, 260, 900, 560],
      [0, 640, 900, 340],
      [60, 0, 840, 900],
      [900, 60, 40, 900],
    ],
    labels: [
      [700, 400, "C3 . 1"],
      [70, 460, "IX"],
      [780, 560, "F0"],
      [110, 500, "004°"],
    ],
  },
} satisfies Record<string, { lines: number[][]; labels: [number, number, string][] }>;

// `variant` picks a distinct line/label layout so two LineField
// instances on the same page (e.g. one per section) never render the
// exact same coordinate text twice -- an earlier pass had "07.2" and
// "LV3" printed verbatim in two different sections, which read as a
// copy-paste bug rather than atmosphere.
export function LineField({
  className = "",
  tone = "light",
  variant = "a",
}: {
  className?: string;
  tone?: "light" | "dark";
  variant?: keyof typeof VARIANTS;
}) {
  const stroke = tone === "light" ? "#f4f5f3" : "#0a0a0b";
  const labelFill = tone === "light" ? "#9a9d9f" : "#5a5c60";
  const { lines, labels } = VARIANTS[variant];

  return (
    <svg
      viewBox="0 0 900 900"
      className={className}
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id={`lf-glow-${tone}`} cx="50%" cy="44%" r="60%">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="30%" stopColor={stroke} stopOpacity="0.12" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`lf-line-${tone}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={stroke} stopOpacity="0" />
          <stop offset="50%" stopColor={stroke} stopOpacity="0.9" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
        <filter id={`lf-bloom-${tone}`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
        <filter id={`lf-soft-${tone}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="0.6" />
        </filter>
      </defs>

      <rect width="900" height="900" fill={`url(#lf-glow-${tone})`} />

      {/* converging diagonal lines, echoing the reference's X/hourglass
          light-lines meeting at a single point of presence -- each
          drawn twice: a wide blurred bloom pass, then a crisp core */}
      {lines.map(([x1, y1, x2, y2], i) => (
        <g key={i} className="linefield-drift" style={{ animationDelay: `${i * -1.7}s` }}>
          <line
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={`url(#lf-line-${tone})`}
            strokeWidth={i === 2 ? 5 : 3}
            filter={`url(#lf-bloom-${tone})`}
          />
          <line
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={`url(#lf-line-${tone})`}
            strokeWidth={i === 2 ? 1.1 : 0.6}
            filter={`url(#lf-soft-${tone})`}
          />
        </g>
      ))}

      {/* scattered coordinate-style readouts along the field -- kept out
          of the corners (0-15% from any edge), which is where real nav
          and hero content sit when this is used as a full-bleed
          background; a label colliding with real UI reads as a bug,
          not atmosphere. */}
      {labels.map(([x, y, label], i) => (
        <text
          key={i}
          x={x}
          y={y}
          fontFamily="var(--font-mono)"
          fontSize="11"
          letterSpacing="1.5"
          fill={labelFill}
        >
          {label}
        </text>
      ))}
    </svg>
  );
}
