import { useLanguage } from "./LanguageContext";

const STYLES: Record<string, string> = {
  VERIFIED_FIXED: "border-temper-500/50 text-temper-300 bg-temper-500/10",
  STILL_VULNERABLE: "border-ember-500/50 text-ember-300 bg-ember-500/10",
  FALSE_POSITIVE: "border-gold-500/50 text-gold-300 bg-gold-500/10",
  INCONCLUSIVE: "border-steel-400/40 text-steel-400 bg-steel-400/10",
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const { t, lang } = useLanguage();
  const cls = STYLES[verdict] ?? STYLES.INCONCLUSIVE;
  const label = t.verdict[verdict] ?? verdict;
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1 text-xs font-semibold tracking-wide uppercase ${cls} ${lang === "ja" ? "font-jp normal-case" : ""}`}
    >
      {label}
    </span>
  );
}
