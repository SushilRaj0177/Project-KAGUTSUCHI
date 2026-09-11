// A grouped instrument-readout block -- the reference board's habit of
// clustering a numeral, a stack of flat color bars, tick marks, and
// mono labels into ONE dense unit (see image 1's top-right cluster:
// "001.04" over a white/magenta/blue/cyan bar stack, dotted grid
// nearby). A handful of isolated icons floating with big gaps between
// them reads as a sparse icon row; this reads as an instrument.
const TONES: Record<string, string> = {
  lime: "var(--mark-lime)",
  magenta: "var(--mark-magenta)",
  cyan: "var(--mark-cyan)",
  blue: "var(--mark-blue)",
  paper: "var(--paper)",
};

export function ReadoutCluster({
  index,
  bars,
  className = "",
}: {
  index: string;
  bars: { tone: keyof typeof TONES; width: number }[];
  className?: string;
}) {
  return (
    <div className={`inline-flex flex-col items-end gap-1.5 ${className}`}>
      <span className="font-mono-tech text-[10px] tracking-[0.15em] opacity-70">{index}</span>
      <div className="flex flex-col items-end gap-0.5">
        {bars.map((bar, i) => (
          <span
            key={i}
            className="block h-[5px]"
            style={{ width: bar.width, background: TONES[bar.tone] }}
          />
        ))}
      </div>
    </div>
  );
}
