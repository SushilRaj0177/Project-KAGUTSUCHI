import { useLanguage } from "./LanguageContext";

const STYLES: Record<string, string> = {
  VERIFIED_FIXED: "border-neon-cyan/60 text-neon-cyan-soft bg-neon-cyan/10 neon-border-cyan",
  STILL_VULNERABLE: "border-neon-pink/60 text-neon-pink-soft bg-neon-pink/10 neon-border-pink",
  FALSE_POSITIVE: "border-dashed border-line-strong text-steel-400",
  INCONCLUSIVE: "border-dotted border-line-strong text-steel-400",
};

const SYMBOLS: Record<string, string> = {
  VERIFIED_FIXED: "✓",
  STILL_VULNERABLE: "✕",
  FALSE_POSITIVE: "○",
  INCONCLUSIVE: "?",
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const { t, lang } = useLanguage();
  const cls = STYLES[verdict] ?? STYLES.INCONCLUSIVE;
  const symbol = SYMBOLS[verdict] ?? SYMBOLS.INCONCLUSIVE;
  const label = t.verdict[verdict] ?? verdict;
  return (
    <span
      className={`inline-flex items-center gap-2 border px-3 py-1 font-mono text-xs font-semibold tracking-wide uppercase ${cls} ${lang === "ja" ? "font-jp normal-case" : ""}`}
    >
      <span aria-hidden="true">{symbol}</span>
      {label}
    </span>
  );
}
