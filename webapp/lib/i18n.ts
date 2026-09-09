export type Lang = "en" | "ja";

export interface Dict {
  tagline: string;
  logLabelEn: string;
  navScan: string;
  navDashboard: string;
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
  heroKanji: string;
  heroTitle: string;
  heroSubtitle: string;
  repoPlaceholder: string;
  scanButton: string;
  scanningButton: string;
  filesScanned: string;
  findingsCount: string;
  noFindings: string;
  noFindingsBody: string;
  verifyButton: string;
  verifyingButton: string;
  attackResult: string;
  proposedFix: string;
  fixUnavailable: string;
  severity: string;
  rationale: string;
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
    navScan: "Scan",
    navDashboard: "Live Runs",
    heroKanji: "鍛・刀",
    heroTitle: "Forge your repo. Find what breaks it.",
    heroSubtitle:
      "Paste any public GitHub repo. Real static analysis, then a real sandboxed exploit, then a real proposed fix — no sample data, no canned demo.",
    repoPlaceholder: "https://github.com/owner/repo",
    scanButton: "Analyze",
    scanningButton: "Scanning…",
    filesScanned: "Python files scanned",
    findingsCount: "Findings",
    noFindings: "No sensitive operations found",
    noFindingsBody: "The scanner checked every Python file in this repo and found nothing matching a known vulnerability class.",
    verifyButton: "Attack & Verify",
    verifyingButton: "Running in sandbox…",
    attackResult: "Attack result",
    proposedFix: "Proposed fix",
    fixUnavailable: "Fix not available",
    severity: "Severity",
    rationale: "Why this was flagged",
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
    navScan: "スキャン",
    navDashboard: "検証記録",
    heroKanji: "鍛・刀",
    heroTitle: "リポジトリを鍛える。弱点を暴く。",
    heroSubtitle:
      "公開GitHubリポジトリのURLを貼るだけ。実際の静的解析、実際のサンドボックス攻撃、実際の修正提案 — サンプルデータも台本もありません。",
    repoPlaceholder: "https://github.com/owner/repo",
    scanButton: "解析する",
    scanningButton: "スキャン中…",
    filesScanned: "スキャンしたPythonファイル数",
    findingsCount: "検出件数",
    noFindings: "危険な処理は見つかりませんでした",
    noFindingsBody: "このリポジトリの全Pythonファイルを検査しましたが、既知の脆弱性クラスに一致するものはありませんでした。",
    verifyButton: "攻撃して検証",
    verifyingButton: "サンドボックス実行中…",
    attackResult: "攻撃結果",
    proposedFix: "修正案",
    fixUnavailable: "修正案なし",
    severity: "深刻度",
    rationale: "検出理由",
  },
};
