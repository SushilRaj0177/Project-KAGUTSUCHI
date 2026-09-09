import { useLanguage } from "./LanguageContext";

const STYLES: Record<string, string> = {
  VERIFIED_FIXED: "bg-paper-50 text-ink-950 border-paper-50",
  STILL_VULNERABLE: "bg-seal-500 text-ink-950 border-seal-500",
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
      className={`inline-flex items-center gap-2 border px-3 py-1 font-mono text-xs font-semibold tracking-wide uppercase ${cls} ${lang === "ja" ? "font-jp normal-case" : ""}`}
    >
      <span aria-hidden="true">{symbol}</span>
      {label}
    </span>
  );
}
