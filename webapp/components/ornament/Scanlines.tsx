// Fixed CRT/surveillance-monitor scanline overlay -- one of the
// concrete things missing from the first two passes that actually
// signals "dystopian screen/system," not just "dark poster."
//
// Deliberately NOT a multiply blend: most of this page is near-black,
// and multiplying anything against black stays black -- the effect was
// completely invisible everywhere except the one pale band. Alternating
// faint light/dark bands with no blend mode (real CRT scanlines are
// both slightly brighter AND slightly darker rows) reads correctly on
// every background.
export function Scanlines() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-40"
      style={{
        backgroundImage:
          "repeating-linear-gradient(180deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, rgba(0,0,0,0.12) 1px, rgba(0,0,0,0.12) 2px, transparent 2px, transparent 3px)",
      }}
    />
  );
}

// Heavy edge vignette -- pulls the corners toward black so the frame
// feels closed-in/surveilled rather than an evenly-lit poster.
export function Vignette() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-30"
      style={{
        background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.55) 100%)",
      }}
    />
  );
}
