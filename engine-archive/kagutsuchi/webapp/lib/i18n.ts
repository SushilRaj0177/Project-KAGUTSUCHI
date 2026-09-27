export type Lang = "en" | "ja";

export interface Dict {
  // Nav
  navScan: string;
  navDashboard: string;
  navCompare: string;
  navCalibration: string;
  navDetectorProposals: string;
  authSignIn: string;
  authSignOut: string;

  // Homepage
  homeStatLabel: string;
  homeHeadline1: string;
  homeHeadline2: string;
  homeHeadline3: string;
  homeSubtitle: string;
  homeCtaScan: string;
  homeCtaLiveRuns: string;
  homeFooterTagline: string;

  // Scan page
  scanPageTitle: string;
  scanPageSubtitle: string;
  repoPlaceholder: string;
  scanButton: string;
  scanningButton: string;
  tryExample: string;
  scanPollingNotice: string;
  filesScanned: string;
  findingsCount: string;
  noFindings: string;
  noFindingsBody: string;
  severityHigh: string;
  severityMedium: string;
  severityLow: string;
  verifyButton: string;
  verifyingButton: string;
  sourceUnavailable: string;
  payloadLabel: string;
  falsePositiveDefault: string;
  proposedFix: string;
  fixUnavailable: string;
  openPrButton: string;
  openingPrButton: string;
  openPrHint: string;
  openPrSignInNudge: string;
  openPrSignedInHint: string;
  openPrTokenPlaceholder: string;
  openPrSubmit: string;
  openPrCancel: string;
  openPrSuccess: string;
  shareResult: string;
  copyPermalink: string;
  permalinkCopied: string;
  copyBadge: string;

  // Permalink page
  permalinkNotFoundBody: string;
  permalinkRunFreshScan: string;
  permalinkFooterNote: string;
  permalinkFooterScanLink: string;

  // Dashboard
  dashboardTitle: string;
  dashboardSubtitle: string;
  emptyTitle: string;
  emptyBodyDashboard: string;
  emptyBodyScanLink: string;
  loading: string;
  statedConfidence: string;
  verdict: Record<string, string>;

  // Calibration
  calibrationTitle: string;
  calibrationSubtitle: string;
  calibrationEmptyBody: string;
  calibrationBrierScore: string;
  calibrationBrierSubtitle: string;
  calibrationSampleCount: string;
  calibrationSamplesShort: string;

  // Detector proposals
  detectorProposalsTitle: string;
  detectorProposalsSubtitle: string;
  detectorProposalsEmptyBody: string;
  detectorProposalsSeenTimes: string;
  approveButton: string;
  approvingButton: string;
  rejectButton: string;
  rejectingButton: string;
  approvedBadge: string;
  revertButton: string;

  // Compare
  compareTitle: string;
  compareSubtitle: string;
  baseRefPlaceholder: string;
  headRefPlaceholder: string;
  compareButton: string;
  comparingButton: string;
  compareAddedTitle: string;
  compareRemovedTitle: string;
  compareNoAdded: string;
  compareNoRemoved: string;
  compareUnchangedCount: string;
  filesScannedShort: string;

  // 404
  notFoundEyebrow: string;
  notFoundTitle: string;
  notFoundBody: string;
  notFoundCta: string;

  vulnClass: Record<string, string>;
}

export const translations: Record<Lang, Dict> = {
  en: {
    navScan: "Scan",
    navDashboard: "Live Runs",
    navCompare: "Compare",
    navCalibration: "Calibration",
    navDetectorProposals: "New Classes",
    authSignIn: "Sign in with GitHub",
    authSignOut: "Sign out",

    homeStatLabel: "exploits proven, not claimed",
    homeHeadline1: "Find the vulnerability.",
    homeHeadline2: "Attack it for real.",
    homeHeadline3: "Prove the fix.",
    homeSubtitle:
      "Kagutsuchi scans your code, then actually exploits what it finds in an isolated sandbox — nothing gets called a vulnerability on a guess, and nothing gets called fixed without a second exploit attempt failing.",
    homeCtaScan: "Run a scan →",
    homeCtaLiveRuns: "See live runs",
    homeFooterTagline: "Detect → Attack → Verify → Fix",

    scanPageTitle: "Scan a public repo",
    scanPageSubtitle: "Paste a GitHub URL. Real static analysis, then a real sandboxed exploit, then a real proposed fix.",
    repoPlaceholder: "https://github.com/owner/repo",
    scanButton: "Analyze",
    scanningButton: "Scanning…",
    tryExample: "Try:",
    scanPollingNotice: "Still scanning — larger repos can take a minute or two.",
    filesScanned: "Files scanned",
    findingsCount: "Findings",
    noFindings: "No findings — nothing in this repo matched a known vulnerability pattern.",
    noFindingsBody: "No findings — nothing in this repo matched a known vulnerability pattern at this commit.",
    severityHigh: "high",
    severityMedium: "medium",
    severityLow: "low",
    verifyButton: "Attack & Verify",
    verifyingButton: "Attacking…",
    sourceUnavailable: "Source unavailable",
    payloadLabel: "payload:",
    falsePositiveDefault: "This finding was a false positive.",
    proposedFix: "Proposed fix",
    fixUnavailable: "Fix not available",
    openPrButton: "Open a PR with this fix",
    openingPrButton: "Opening…",
    openPrHint:
      "Uses a GitHub token with repo write access, sent directly to GitHub for this one request — never stored.",
    openPrSignInNudge: "Sign in with GitHub",
    openPrSignedInHint: "Opens the PR as your signed-in GitHub account.",
    openPrTokenPlaceholder: "GitHub personal access token (repo scope)",
    openPrSubmit: "Create pull request",
    openPrCancel: "Cancel",
    openPrSuccess: "Pull request opened ↗",
    shareResult: "Share this result:",
    copyPermalink: "Copy permalink",
    permalinkCopied: "Copied!",
    copyBadge: "Copy README badge",

    permalinkNotFoundBody: "This exact commit hasn't been scanned yet.",
    permalinkRunFreshScan: "Run a fresh scan",
    permalinkFooterNote: "This is a shared permalink for a scan already run against this exact commit —",
    permalinkFooterScanLink: "scan a repo",

    dashboardTitle: "Live runs",
    dashboardSubtitle: "Real completed verifications from actual site usage — not sample data.",
    emptyTitle: "No runs recorded yet",
    emptyBodyDashboard: "Attack a finding on the",
    emptyBodyScanLink: "scan page",
    loading: "Loading…",
    statedConfidence: "stated confidence",
    verdict: {
      VERIFIED_FIXED: "Verified Fixed",
      STILL_VULNERABLE: "Still Vulnerable",
      FALSE_POSITIVE: "False Positive",
      INCONCLUSIVE: "Inconclusive",
    },

    calibrationTitle: "Is the AI's confidence trustworthy?",
    calibrationSubtitle:
      "Every attack payload comes with the model's own stated confidence. This scores that confidence against what the sandbox actually observed, from real production runs.",
    calibrationEmptyBody: "No calibration data yet — run an attack on the",
    calibrationBrierScore: "Brier score — 0 is perfectly calibrated, 1 is worst",
    calibrationBrierSubtitle: "from {n} real attacks",
    calibrationSampleCount: "Samples",
    calibrationSamplesShort: "samples",

    detectorProposalsTitle: "New vulnerability classes",
    detectorProposalsSubtitle:
      "The AI scanner reads code for meaning, not just fixed patterns. When it thinks it's found a vulnerability class outside the deterministic scanner's known list, it lands here. Approving one starts checking for it on every future scan immediately — still just a dotted call name matched the same way as every built-in check, never AI-generated code running unreviewed.",
    detectorProposalsEmptyBody:
      "No proposals yet. Scan a repo whose vulnerabilities don't fit the known classes and the AI pass will surface one here.",
    detectorProposalsSeenTimes: "seen {n}×",
    approveButton: "Approve — check for this on every scan",
    approvingButton: "Approving…",
    rejectButton: "Reject",
    rejectingButton: "Rejecting…",
    approvedBadge: "Approved — live on every scan",
    revertButton: "Revert",

    compareTitle: "Compare two branches",
    compareSubtitle: "Did this branch or PR introduce a new vulnerability — or fix one? Scans both refs and diffs the findings.",
    baseRefPlaceholder: "base ref (e.g. main)",
    headRefPlaceholder: "head ref (e.g. my-branch)",
    compareButton: "Compare",
    comparingButton: "Comparing…",
    compareAddedTitle: "Added",
    compareRemovedTitle: "Removed",
    compareNoAdded: "No new findings introduced.",
    compareNoRemoved: "No findings fixed between these refs.",
    compareUnchangedCount: "finding(s) unchanged between refs.",
    filesScannedShort: "files scanned",

    notFoundEyebrow: "404",
    notFoundTitle: "Nothing here.",
    notFoundBody: "This page doesn't exist — or a scan permalink pointed at a commit that was never scanned.",
    notFoundCta: "Run a scan →",

    vulnClass: {
      shell_exec: "Command Injection",
      subprocess: "Command Injection",
      sql_query: "SQL Injection",
      deserialization: "Insecure Deserialization",
      filesystem: "Path Traversal",
      auth_change: "Authentication Bypass",
      network_egress: "Unsafe Network Access",
      other: "Security Vulnerability",
    },
  },
  ja: {
    navScan: "スキャン",
    navDashboard: "検証記録",
    navCompare: "比較",
    navCalibration: "信頼度検証",
    navDetectorProposals: "新規クラス",
    authSignIn: "GitHubでサインイン",
    authSignOut: "サインアウト",

    homeStatLabel: "件の実証済みエクスプロイト（主張ではなく証明）",
    homeHeadline1: "脆弱性を見つける。",
    homeHeadline2: "実際に攻撃する。",
    homeHeadline3: "修正を証明する。",
    homeSubtitle:
      "Kagutsuchiはコードをスキャンし、見つけた脆弱性を隔離されたサンドボックス内で実際に攻撃します — 推測で脆弱性と呼ぶことはなく、再攻撃が失敗しない限り修正済みとも呼びません。",
    homeCtaScan: "スキャンを実行 →",
    homeCtaLiveRuns: "検証記録を見る",
    homeFooterTagline: "検出 → 攻撃 → 検証 → 修正",

    scanPageTitle: "公開リポジトリをスキャン",
    scanPageSubtitle: "GitHubのURLを貼り付けてください。実際の静的解析、実際のサンドボックス攻撃、実際の修正案が続きます。",
    repoPlaceholder: "https://github.com/owner/repo",
    scanButton: "解析する",
    scanningButton: "スキャン中…",
    tryExample: "試す：",
    scanPollingNotice: "スキャン中です — 大きなリポジトリは1〜2分かかることがあります。",
    filesScanned: "スキャン済みファイル数",
    findingsCount: "検出件数",
    noFindings: "検出結果なし — このリポジトリには既知の脆弱性パターンに一致するものがありませんでした。",
    noFindingsBody: "検出結果なし — このコミットには既知の脆弱性パターンに一致するものがありませんでした。",
    severityHigh: "高",
    severityMedium: "中",
    severityLow: "低",
    verifyButton: "攻撃して検証",
    verifyingButton: "攻撃中…",
    sourceUnavailable: "ソース取得不可",
    payloadLabel: "ペイロード：",
    falsePositiveDefault: "この検出結果は誤検知でした。",
    proposedFix: "修正案",
    fixUnavailable: "修正案なし",
    openPrButton: "この修正でPRを作成",
    openingPrButton: "PR作成中…",
    openPrHint: "リポジトリへの書き込み権限を持つGitHubトークンを使用します。このリクエストのみに使われ、保存はされません。",
    openPrSignInNudge: "GitHubでサインイン",
    openPrSignedInHint: "サインイン中のGitHubアカウントとしてPRを作成します。",
    openPrTokenPlaceholder: "GitHubパーソナルアクセストークン（repoスコープ）",
    openPrSubmit: "プルリクエストを作成",
    openPrCancel: "キャンセル",
    openPrSuccess: "プルリクエストを作成しました ↗",
    shareResult: "この結果を共有：",
    copyPermalink: "リンクをコピー",
    permalinkCopied: "コピーしました！",
    copyBadge: "READMEバッジをコピー",

    permalinkNotFoundBody: "このコミットはまだスキャンされていません。",
    permalinkRunFreshScan: "新しくスキャンを実行",
    permalinkFooterNote: "これはこのコミットに対して既に実行されたスキャンの共有リンクです —",
    permalinkFooterScanLink: "リポジトリをスキャン",

    dashboardTitle: "検証記録",
    dashboardSubtitle: "実際のサイト利用から得られた検証結果です — サンプルデータではありません。",
    emptyTitle: "検証記録なし",
    emptyBodyDashboard: "作成するには、",
    emptyBodyScanLink: "スキャンページ",
    loading: "読み込み中…",
    statedConfidence: "申告された信頼度",
    verdict: {
      VERIFIED_FIXED: "修正確認",
      STILL_VULNERABLE: "未修正",
      FALSE_POSITIVE: "誤検知",
      INCONCLUSIVE: "判定不能",
    },

    calibrationTitle: "AIの自信は信頼できるか？",
    calibrationSubtitle:
      "すべての攻撃ペイロードには、モデル自身が申告した信頼度が付いています。このページでは、その信頼度と実際の本番環境でサンドボックスが観測した結果を比較します。",
    calibrationEmptyBody: "まだ検証データがありません — ",
    calibrationBrierScore: "ブライアスコア — 0が完璧、1が最悪",
    calibrationBrierSubtitle: "{n}件の実際の攻撃から算出",
    calibrationSampleCount: "サンプル数",
    calibrationSamplesShort: "件",

    detectorProposalsTitle: "新しい脆弱性クラス",
    detectorProposalsSubtitle:
      "AIスキャナーは固定パターンだけでなく、コードの意味を読み取ります。決定論的スキャナーの既知リストにない脆弱性クラスを見つけたと判断すると、ここに表示されます。承認すると即座に今後のすべてのスキャンで検出対象になります — それでも単なるドット区切りの呼び出し名を、既存の組み込みチェックと全く同じ方法で照合するだけであり、未レビューのAI生成コードが実行されることは決してありません。",
    detectorProposalsEmptyBody:
      "まだ提案はありません。既知のクラスに当てはまらない脆弱性を持つリポジトリをスキャンすると、AIパスがここに提案を表示します。",
    detectorProposalsSeenTimes: "{n}回検出",
    approveButton: "承認 — 今後すべてのスキャンで検出",
    approvingButton: "承認中…",
    rejectButton: "却下",
    rejectingButton: "却下中…",
    approvedBadge: "承認済み — 全スキャンで有効",
    revertButton: "取り消し",

    compareTitle: "2つのブランチを比較",
    compareSubtitle: "このブランチやPRが新しい脆弱性を持ち込んだのか、それとも修正したのかを確認します。両方のリファレンスをスキャンし、検出結果を比較します。",
    baseRefPlaceholder: "ベースリファレンス（例: main）",
    headRefPlaceholder: "比較対象のリファレンス（例: my-branch）",
    compareButton: "比較する",
    comparingButton: "比較中…",
    compareAddedTitle: "追加された検出結果",
    compareRemovedTitle: "修正された検出結果",
    compareNoAdded: "新しい検出結果はありません。",
    compareNoRemoved: "この2つの間で修正された検出結果はありません。",
    compareUnchangedCount: "件の検出結果は変化ありません。",
    filesScannedShort: "ファイルをスキャン",

    notFoundEyebrow: "404",
    notFoundTitle: "何もありません。",
    notFoundBody: "このページは存在しません — または、まだスキャンされていないコミットへのパーマリンクです。",
    notFoundCta: "スキャンを実行 →",

    vulnClass: {
      shell_exec: "コマンドインジェクション",
      subprocess: "コマンドインジェクション",
      sql_query: "SQLインジェクション",
      deserialization: "安全でないデシリアライゼーション",
      filesystem: "パストラバーサル",
      auth_change: "認証バイパス",
      network_egress: "危険なネットワークアクセス",
      other: "セキュリティ脆弱性",
    },
  },
};
