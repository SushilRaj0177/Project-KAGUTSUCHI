export function Marquee({ text }: { text: string }) {
  const item = (
    <span className="mx-4 flex items-center gap-4 font-display text-2xl font-extrabold tracking-tight whitespace-nowrap uppercase">
      {text}
      <span className="text-seal-500">●</span>
    </span>
  );
  return (
    <div className="overflow-hidden border-y border-line py-4">
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
