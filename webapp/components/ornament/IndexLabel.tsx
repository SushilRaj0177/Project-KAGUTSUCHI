// Coordinate-style mono label -- "001.04", "P0", "LV7", "D1" from the
// reference boards. Used to give panels/sections an instrument-readout
// identity rather than a plain heading.
export function IndexLabel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`font-mono-tech text-[10px] text-[var(--steel-500)] uppercase ${className}`}>{children}</span>
  );
}
