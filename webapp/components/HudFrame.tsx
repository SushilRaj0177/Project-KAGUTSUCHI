export function HudFrame() {
  const corner = "absolute h-5 w-5 border-neon-cyan/70";
  return (
    <div className="pointer-events-none fixed inset-4 z-20 md:inset-6">
      <span className={`${corner} top-0 left-0 border-t-2 border-l-2`} />
      <span className={`${corner} top-0 right-0 border-t-2 border-r-2`} />
      <span className={`${corner} bottom-0 left-0 border-b-2 border-l-2`} />
      <span className={`${corner} right-0 bottom-0 border-r-2 border-b-2`} />
    </div>
  );
}
