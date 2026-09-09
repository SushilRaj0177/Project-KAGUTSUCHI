const STYLES: Record<string, { label: string; jp: string; cls: string }> = {
  VERIFIED_FIXED: {
    label: "Verified Fixed",
    jp: "修正確認",
    cls: "border-temper-500/50 text-temper-300 bg-temper-500/10",
  },
  STILL_VULNERABLE: {
    label: "Still Vulnerable",
    jp: "未修正",
    cls: "border-ember-500/50 text-ember-300 bg-ember-500/10",
  },
  FALSE_POSITIVE: {
    label: "False Positive",
    jp: "誤検知",
    cls: "border-gold-500/50 text-gold-300 bg-gold-500/10",
  },
  INCONCLUSIVE: {
    label: "Inconclusive",
    jp: "判定不能",
    cls: "border-steel-400/40 text-steel-400 bg-steel-400/10",
  },
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const style = STYLES[verdict] ?? STYLES.INCONCLUSIVE;
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1 text-xs font-semibold tracking-wide ${style.cls}`}
    >
      <span className="font-jp text-[11px]">{style.jp}</span>
      <span className="uppercase">{style.label}</span>
    </span>
  );
}
