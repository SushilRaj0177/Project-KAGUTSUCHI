// The small flat-color marks from the reference boards (a lime tick, a
// magenta chip, a cyan sliver) -- here given real semantic meaning
// instead of decoration: severity/verdict signal. This is the ONLY
// place color appears with any weight; everywhere else is greyscale.
const TONES = {
  lime: "var(--mark-lime)", // verified / safe / low severity
  magenta: "var(--mark-magenta)", // high severity / failed / alert
  cyan: "var(--mark-cyan)", // running / info
  blue: "var(--mark-blue)", // medium severity / neutral signal
} as const;

export function AccentChip({
  tone,
  className = "",
}: {
  tone: keyof typeof TONES;
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-2 w-2 shrink-0 ${className}`}
      style={{ background: TONES[tone] }}
    />
  );
}

export function AccentBar({ tone, className = "" }: { tone: keyof typeof TONES; className?: string }) {
  return <span aria-hidden="true" className={`inline-block h-1 w-6 shrink-0 ${className}`} style={{ background: TONES[tone] }} />;
}
