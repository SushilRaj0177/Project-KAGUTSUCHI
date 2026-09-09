export function RevealText({ text, startDelay = 0 }: { text: string; startDelay?: number }) {
  const words = text.split(" ");
  return (
    <>
      {words.map((word, i) => (
        <span key={i} className="overflow-hidden" style={{ display: "inline-block" }}>
          <span
            className="reveal-word"
            style={{ animationDelay: `${startDelay + i * 0.06}s` }}
          >
            {word}
            {i < words.length - 1 ? " " : ""}
          </span>
        </span>
      ))}
    </>
  );
}
