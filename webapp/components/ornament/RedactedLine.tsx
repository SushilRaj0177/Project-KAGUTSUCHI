// A line of "classified document" redaction bars -- black blocks
// standing in for censored text, at varying widths. A strong,
// immediately-legible surveillance-state/dystopian motif that neither
// prior pass used at all.
export function RedactedLine({ widths, className = "" }: { widths: number[]; className?: string }) {
  return (
    <div className={`flex items-center gap-1.5 ${className}`} aria-hidden="true">
      {widths.map((w, i) => (
        <span key={i} className="block h-3" style={{ width: w, background: "currentColor" }} />
      ))}
    </div>
  );
}
