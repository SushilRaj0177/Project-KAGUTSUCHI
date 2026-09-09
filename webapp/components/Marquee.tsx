export function Marquee({ text }: { text: string }) {
  const item = (
    <span className="mx-4 flex items-center gap-4 font-display text-2xl font-extrabold tracking-tight whitespace-nowrap uppercase">
      <span className="neon-text-cyan">{text}</span>
      <span className="text-neon-pink">◆</span>
    </span>
  );
  return (
    <div className="relative z-10 overflow-hidden border-y border-line py-4">
      <div className="marquee-track">
        {item}
        {item}
        {item}
        {item}
        {item}
        {item}
        {item}
        {item}
      </div>
    </div>
  );
}
