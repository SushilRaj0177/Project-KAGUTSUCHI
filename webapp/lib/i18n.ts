export type Lang = "en" | "ja";

export interface Dict {
  tagline: string;
  logLabelEn: string;
  statTotal: string;
  statVerified: string;
  statVulnerable: string;
  verdict: Record<string, string>;
  finding: string;
  hypothesis: string;
  before: string;
  after: string;
  exitCode: string;
  markerCreated: string;
  none: string;
  emptyTitle: string;
  emptyBody: string;
}

export const translations: Record<Lang, Dict> = {
  en: {
    tagline: "Autonomous code integrity verification — proof, not opinion.",
    logLabelEn: "Verification Log",
    statTotal: "Total Runs",
    statVerified: "Verified Fixed",
    statVulnerable: "Still Vulnerable",
    verdict: {
      VERIFIED_FIXED: "Verified Fixed",
      STILL_VULNERABLE: "Still Vulnerable",
      FALSE_POSITIVE: "False Positive",
      INCONCLUSIVE: "Inconclusive",
    },
    finding: "Finding",
    hypothesis: "Hypothesis",
    before: "Before",
    after: "After",
    exitCode: "Exit code",
    markerCreated: "Marker created",
    none: "none",
    emptyTitle: "No runs recorded yet",
    emptyBody:
      "This dashboard only shows real verification runs — nothing here is sample data. Run the pipeline and publish a result to see it appear:",
  },
  ja: {
    tagline: "自律型コード整合性検証 — 意見ではなく、証明。",
    logLabelEn: "検証記録",
    statTotal: "総検証数",
    statVerified: "修正確認",
    statVulnerable: "未修正",
    verdict: {
      VERIFIED_FIXED: "修正確認",
      STILL_VULNERABLE: "未修正",
      FALSE_POSITIVE: "誤検知",
      INCONCLUSIVE: "判定不能",
    },
    finding: "検知箇所",
    hypothesis: "攻撃仮説",
    before: "修正前",
    after: "修正後",
    exitCode: "終了コード",
    markerCreated: "検出ファイル",
    none: "なし",
    emptyTitle: "検証記録なし",
    emptyBody:
      "このダッシュボードは実際の検証結果のみを表示します。サンプルデータは一切ありません。パイプラインを実行し、結果を公開してください：",
  },
};
