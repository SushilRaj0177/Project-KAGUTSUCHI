import { useLanguage } from "./LanguageContext";

// Status reads through weight, fill, and symbol -- never color.
const STYLES: Record<string, string> = {
  VERIFIED_FIXED: "bg-paper-50 text-ink-950 border-paper-50",
  STILL_VULNERABLE: "border-2 border-paper-50 text-paper-50",
  FALSE_POSITIVE: "border border-dashed border-line-strong text-steel-400",
  INCONCLUSIVE: "border border-dotted border-line-strong text-steel-400",
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
      className={`inline-flex items-center gap-2 px-3 py-1 font-mono text-xs font-semibold tracking-wide uppercase ${cls} ${lang === "ja" ? "font-jp normal-case" : ""}`}
    >
      <span aria-hidden="true">{symbol}</span>
      {label}
    </span>
  );
}
