// Fine film-grain over the whole page -- a fixed, full-viewport SVG
// noise filter at very low opacity (see .grain-overlay in globals.css).
// This is what keeps large flat dark panels from looking like plain
// digital black; the reference photography reads as grainy/painterly
// even in its darkest passages.
export function Grain() {
  return (
    <svg className="grain-overlay" aria-hidden="true">
      <filter id="kagutsuchi-grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#kagutsuchi-grain)" />
    </svg>
  );
}
