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
  truncatedNotice: string;
  noFindings: string;
  noFindingsBody: string;
  verifyButton: string;
  verifyingButton: string;
  attackResult: string;
  proposedFix: string;
  fixUnavailable: string;
  severity: string;
  rationale: string;
  vulnClass: Record<string, string>;
  whatHappened: string;
  plainVerifiedFixed: string;
  plainStillVulnerable: string;
  plainOther: string;
  technicalDetails: string;
  vulnerableCode: string;
  backendOnline: string;
  backendOffline: string;
  backendOfflineDetail: string;
  reducedIsolationNotice: string;
  tryExample: string;
  cachedNotice: string;
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
    truncatedNotice:
      "This repo has more Python files than we scan per request — results below are from the first 300 files found, not the whole repo.",
    noFindings: "No sensitive operations found",
    noFindingsBody: "The scanner checked every Python file in this repo and found nothing matching a known vulnerability class.",
    verifyButton: "Attack & Verify",
    verifyingButton: "Running in sandbox…",
    attackResult: "Attack result",
    proposedFix: "Proposed fix",
    fixUnavailable: "Fix not available",
    severity: "Severity",
    rationale: "Why this is dangerous",
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
    whatHappened: "What happened",
    plainVerifiedFixed:
      "We attacked this code for real, in an isolated sandbox — the attack worked. We then tried the exact same attack against the fixed version — it was blocked. The fix is verified.",
    plainStillVulnerable:
      "We attacked this code for real, in an isolated sandbox — the attack worked, and it still works after the proposed fix. This is not safe yet.",
    plainOther: "We attacked this code for real, in an isolated sandbox. See the technical details below for exactly what happened.",
    technicalDetails: "Technical details (for the curious)",
    vulnerableCode: "The vulnerable code",
    backendOnline: "Backend online",
    backendOffline: "Backend offline",
    backendOfflineDetail: "The scanning backend is unreachable right now — repo scans won't work until it's back.",
    reducedIsolationNotice:
      "This host has no Docker available, so this attack ran with reduced isolation (a locked-down subprocess, not a full container) instead of our usual sandbox.",
    tryExample: "Try:",
    cachedNotice: "// served from cache — same commit already scanned",
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
    truncatedNotice:
      "このリポジトリは1回のスキャン上限を超えるPythonファイルを含んでいます — 以下の結果は最初に見つかった300ファイルのみを対象としており、リポジトリ全体ではありません。",
    noFindings: "危険な処理は見つかりませんでした",
    noFindingsBody: "このリポジトリの全Pythonファイルを検査しましたが、既知の脆弱性クラスに一致するものはありませんでした。",
    verifyButton: "攻撃して検証",
    verifyingButton: "サンドボックス実行中…",
    attackResult: "攻撃結果",
    proposedFix: "修正案",
    fixUnavailable: "修正案なし",
    severity: "深刻度",
    rationale: "危険な理由",
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
    whatHappened: "何が起きたか",
    plainVerifiedFixed:
      "このコードに対して、隔離されたサンドボックス内で実際に攻撃を行いました — 攻撃は成功しました。次に、修正後のバージョンに全く同じ攻撃を試しました — 今度はブロックされました。修正は確認済みです。",
    plainStillVulnerable:
      "このコードに対して、隔離されたサンドボックス内で実際に攻撃を行いました — 攻撃は成功し、提案された修正後も依然として成功します。まだ安全ではありません。",
    plainOther: "このコードに対して、隔離されたサンドボックス内で実際に攻撃を行いました。詳細は下記の技術情報をご覧ください。",
    technicalDetails: "技術詳細（興味のある方向け）",
    vulnerableCode: "脆弱なコード",
    backendOnline: "バックエンド稼働中",
    backendOffline: "バックエンドオフライン",
    backendOfflineDetail: "現在スキャン用のバックエンドに接続できません — 復旧するまでリポジトリのスキャンはできません。",
    reducedIsolationNotice:
      "このホストではDockerが利用できないため、通常のサンドボックスの代わりに制限付きサブプロセスで攻撃を実行しました（完全なコンテナ分離ではありません）。",
    tryExample: "試す：",
    cachedNotice: "// キャッシュから表示 — 同じコミットは既にスキャン済みです",
  },
};
