export type Lang = "en" | "ja";

export interface Dict {
  tagline: string;
  logLabelEn: string;
  navHome: string;
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
  openPrButton: string;
  openingPrButton: string;
  openPrHint: string;
  openPrTokenPlaceholder: string;
  openPrSubmit: string;
  openPrCancel: string;
  openPrSuccess: string;
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
  filterSearchPlaceholder: string;
  downloadReport: string;
  noFindingsMatchFilter: string;
  copyPermalink: string;
  permalinkCopied: string;
  permalinkNotFoundTitle: string;
  permalinkNotFoundBody: string;
  copyBadge: string;
  navCompare: string;
  compareTitle: string;
  compareSubtitle: string;
  baseRefPlaceholder: string;
  headRefPlaceholder: string;
  compareButton: string;
  comparingButton: string;
  compareAdded: string;
  compareRemoved: string;
  compareUnchanged: string;
  compareAddedTitle: string;
  compareRemovedTitle: string;
  compareNoDiff: string;
  navCalibration: string;
  calibrationTitle: string;
  calibrationSubtitle: string;
  calibrationEmptyTitle: string;
  calibrationEmptyBody: string;
  calibrationSampleSize: string;
  calibrationBrierScore: string;
  calibrationBuckets: string;
  modelStatedConfidence: string;
  navDetectorProposals: string;
  detectorProposalsTitle: string;
  detectorProposalsSubtitle: string;
  detectorProposalsEmptyTitle: string;
  detectorProposalsEmptyBody: string;
  detectorProposalsSeenTimes: string;
  detectorProposalsSpottedIn: string;

  // Landing page
  landingTitleLine1: string;
  landingTitleLine1Accent: string;
  landingTitleLine2: string;
  landingTitleLine2Accent: string;
  landingSubtitle: string;
  landingCtaScan: string;
  landingCtaDashboard: string;
  landingStat1Value: string;
  landingStat1Label: string;
  landingStat2Value: string;
  landingStat2Label: string;
  landingStat3Value: string;
  landingStat3Label: string;
  landingStat4Value: string;
  landingStat4Label: string;
  nameEyebrow: string;
  nameTitle: string;
  nameBodyPart1: string;
  nameBodyPart2: string;
  nameBodyPart3: string;
  featuresEyebrow: string;
  featuresTitle: string;
  featuresSubtitle: string;
  feature1Kanji: string;
  feature1Title: string;
  feature1Body: string;
  feature2Kanji: string;
  feature2Title: string;
  feature2Body: string;
  feature3Kanji: string;
  feature3Title: string;
  feature3Body: string;
  feature4Kanji: string;
  feature4Title: string;
  feature4Body: string;
  flowEyebrow: string;
  flowTitle: string;
  flowSubtitle: string;
  flowStep1: string;
  flowStep2: string;
  flowStep3: string;
  flowStep4: string;
  landingFooterTitle: string;
  landingFooterCta: string;
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
    navHome: "Home",
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
    openPrButton: "Open a PR with this fix",
    openingPrButton: "Opening PR…",
    openPrHint: "Uses a GitHub token with repo write access, sent directly to GitHub for this one request — never stored, never logged.",
    openPrTokenPlaceholder: "GitHub personal access token (repo scope)",
    openPrSubmit: "Create pull request",
    openPrCancel: "Cancel",
    openPrSuccess: "Pull request opened",
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
    filterSearchPlaceholder: "Filter by file or function name…",
    downloadReport: "Download report",
    noFindingsMatchFilter: "No findings match this filter.",
    copyPermalink: "Copy permalink",
    permalinkCopied: "Copied!",
    permalinkNotFoundTitle: "No cached scan for this commit",
    permalinkNotFoundBody:
      "This exact commit hasn't been scanned yet, so there's nothing to show here. Run a live scan on the homepage instead.",
    copyBadge: "Copy README badge",
    navCompare: "Compare",
    compareTitle: "Compare two branches",
    compareSubtitle:
      "Scan two refs of the same repo and see exactly which findings a branch or PR added or fixed — real for gating merges on new vulnerabilities, not just eyeballing two separate scans.",
    baseRefPlaceholder: "base branch, e.g. main",
    headRefPlaceholder: "head branch / PR branch",
    compareButton: "Compare",
    comparingButton: "Scanning both…",
    compareAdded: "New findings",
    compareRemoved: "Fixed findings",
    compareUnchanged: "Unchanged",
    compareAddedTitle: "Introduced by this branch",
    compareRemovedTitle: "Fixed by this branch",
    compareNoDiff: "No difference in findings between these two refs.",
    navCalibration: "Calibration",
    calibrationTitle: "Is the model's confidence trustworthy?",
    calibrationSubtitle:
      "Every attack hypothesis includes the model's own stated confidence that its exact payload would succeed. This page compares that confidence against real sandbox outcomes from live site usage — not a mocked test, actual production data.",
    calibrationEmptyTitle: "No calibration data yet",
    calibrationEmptyBody:
      "This fills in as real Attack & Verify runs complete on the site — nothing here is sample data.",
    calibrationSampleSize: "Samples",
    calibrationBrierScore: "Brier score (0 = perfect)",
    calibrationBuckets: "Confidence deciles",
    modelStatedConfidence: "Model's stated confidence in this payload",
    navDetectorProposals: "New Classes",
    detectorProposalsTitle: "AI-discovered vulnerability classes",
    detectorProposalsSubtitle:
      "Our deterministic scanner only catches a fixed list of patterns. When the AI scan spots a genuinely different, reusable vulnerability signature — not just a one-off guess — it proposes it here as a candidate for the deterministic list. Nothing here is auto-applied: a person reviews each one and promotes it deliberately (scripts/promote_detector.py), the same way every hand-authored detector in this project got added. This is how the deterministic strategy keeps expanding without ever trusting an AI claim outright.",
    detectorProposalsEmptyTitle: "No new classes proposed yet",
    detectorProposalsEmptyBody:
      "This fills in as real scans turn up vulnerability patterns outside the current detector list — nothing here is sample data.",
    detectorProposalsSeenTimes: "seen {n}×",
    detectorProposalsSpottedIn: "Spotted in",

    landingTitleLine1: "Exploits you can",
    landingTitleLine1Accent: "prove.",
    landingTitleLine2: "Fixes you can",
    landingTitleLine2Accent: "trust.",
    landingSubtitle:
      "KAGUTSUCHI finds vulnerabilities with static rules and an AI scan, then actually attacks your code in an isolated sandbox to prove it — and proves the fix the same way, by attacking it again. No guesses, no canned demos.",
    landingCtaScan: "> Run a scan",
    landingCtaDashboard: "> See live runs",
    landingStat1Value: "5",
    landingStat1Label: "Vulnerability classes",
    landingStat2Value: "2",
    landingStat2Label: "Detection engines",
    landingStat3Value: "100%",
    landingStat3Label: "Sandboxed execution",
    landingStat4Value: "0",
    landingStat4Label: "Unverified verdicts",
    nameEyebrow: "The name",
    nameTitle: "Why “Kagutsuchi”?",
    nameBodyPart1:
      "Kagutsuchi (迦具土) is the Shinto god of fire in Japanese mythology — born in fire so fierce it fatally burned his own mother, and later slain by his own father in grief. Fire, in that story, is never gentle: it's the same force that forges a blade and the one that destroys what touches it carelessly.",
    nameBodyPart2:
      "That duality is why we borrowed the name. This engine doesn't guess whether your code is safe — it puts it in the fire. A real attack, run for real, against the real code. What survives that fire is verified. What doesn't was never safe to begin with.",
    nameBodyPart3:
      "A proposed fix goes through the same fire a second time, with the identical payload. “Verified Fixed” only ever means one thing here: we attacked it again, and this time it held.",
    featuresEyebrow: "What it actually does",
    featuresTitle: "Every layer is real, not simulated.",
    featuresSubtitle: "Static rules and an AI scan surface candidates. Nothing is trusted until it's watched happening.",
    feature1Kanji: "検",
    feature1Title: "Two detection engines",
    feature1Body:
      "A deterministic scanner matches known dangerous call patterns; an AI pass reads the code for meaning and catches classes the fixed list doesn't know about yet — command injection, SQL injection, insecure deserialization, path traversal, unsafe archive extraction, and more.",
    feature2Kanji: "攻",
    feature2Title: "Real sandboxed attacks",
    feature2Body:
      "Every finding gets an actual exploit attempt in an isolated, network-disabled sandbox. If it doesn't create real, observable proof of compromise, it's marked a false positive — not a hunch dressed up as a verdict.",
    feature3Kanji: "治",
    feature3Title: "Fixes verified, not assumed",
    feature3Body:
      "A proposed fix gets attacked with the exact same payload before anyone calls it fixed. “Verified Fixed” means the exploit was tried again against the fix and it failed — an outcome, not a claim.",
    feature4Kanji: "拡",
    feature4Title: "The detector list keeps growing",
    feature4Body:
      "When the AI spots a vulnerability pattern outside the known list, it's queued for human review as a New Class — never auto-trusted, but never silently missed either.",
    flowEyebrow: "The pipeline",
    flowTitle: "From a repo URL to a proven verdict.",
    flowSubtitle: "Scan → hypothesize → attack → fix → verify.",
    flowStep1: "Paste a public GitHub repo URL — a deterministic scanner and an AI pass both look for real vulnerabilities.",
    flowStep2: "Pick a finding — an attack payload is generated specifically for that code, not a generic template.",
    flowStep3: "The payload runs for real, in an isolated sandbox — the result is observed, not asserted.",
    flowStep4: "If it worked, a fix is proposed and attacked with the same payload again — the verdict is whatever actually happened.",
    landingFooterTitle: "Paste a repo. Watch it happen.",
    landingFooterCta: "> Run a scan",
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
    navHome: "ホーム",
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
    openPrButton: "この修正でPRを作成",
    openingPrButton: "PR作成中…",
    openPrHint: "リポジトリへの書き込み権限を持つGitHubトークンを使用します。このリクエストのみに使われ、保存もログ記録もされません。",
    openPrTokenPlaceholder: "GitHubパーソナルアクセストークン（repoスコープ）",
    openPrSubmit: "プルリクエストを作成",
    openPrCancel: "キャンセル",
    openPrSuccess: "プルリクエストを作成しました",
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
    filterSearchPlaceholder: "ファイル名または関数名で絞り込み…",
    downloadReport: "レポートをダウンロード",
    noFindingsMatchFilter: "この条件に一致する検出結果はありません。",
    copyPermalink: "リンクをコピー",
    permalinkCopied: "コピーしました！",
    permalinkNotFoundTitle: "このコミットのキャッシュはありません",
    permalinkNotFoundBody:
      "このコミットはまだスキャンされていないため、表示できる内容がありません。トップページで実際にスキャンを実行してください。",
    copyBadge: "READMEバッジをコピー",
    navCompare: "比較",
    compareTitle: "2つのブランチを比較",
    compareSubtitle:
      "同じリポジトリの2つのブランチをスキャンし、そのブランチやPRが追加または修正した検出結果を正確に把握できます。2つのスキャン結果を目で見比べるのではなく、新しい脆弱性でマージをブロックする用途に使えます。",
    baseRefPlaceholder: "ベースブランチ（例: main）",
    headRefPlaceholder: "比較対象のブランチ / PRブランチ",
    compareButton: "比較する",
    comparingButton: "両方スキャン中…",
    compareAdded: "新規検出",
    compareRemoved: "修正された検出",
    compareUnchanged: "変化なし",
    compareAddedTitle: "このブランチで新たに追加された脆弱性",
    compareRemovedTitle: "このブランチで修正された脆弱性",
    compareNoDiff: "この2つのブランチ間で検出結果に差はありません。",
    navCalibration: "信頼度検証",
    calibrationTitle: "モデルの自信は信頼できるか？",
    calibrationSubtitle:
      "すべての攻撃仮説には、そのペイロードが成功するというモデル自身の信頼度が含まれています。このページでは、その信頼度と実際のサンドボックスでの結果（モックではなく実際の本番データ）を比較します。",
    calibrationEmptyTitle: "まだ検証データがありません",
    calibrationEmptyBody:
      "サイト上で実際の攻撃・検証が完了するたびにここにデータが蓄積されます — サンプルデータは一切ありません。",
    calibrationSampleSize: "サンプル数",
    calibrationBrierScore: "ブライアスコア（0が完璧）",
    calibrationBuckets: "信頼度の分布",
    modelStatedConfidence: "このペイロードに対するモデルの自己申告信頼度",
    navDetectorProposals: "新規クラス",
    detectorProposalsTitle: "AIが発見した脆弱性クラス",
    detectorProposalsSubtitle:
      "決定論的スキャナーは固定されたパターンのリストしか検出できません。AIスキャンが単なる思いつきではなく、本当に新しい、再利用可能な脆弱性シグネチャを見つけた場合、ここに決定論的リストへの候補として提案されます。ここに表示されるものは自動適用されません — 人間が個別に確認し、意図的に採用します（scripts/promote_detector.py）。このプロジェクトで手動作成されたすべての検出ルールと同じプロセスです。AIの主張を無条件に信頼することなく、決定論的な検出手法を拡張し続ける仕組みです。",
    detectorProposalsEmptyTitle: "まだ新しいクラスは提案されていません",
    detectorProposalsEmptyBody:
      "実際のスキャンで既存の検出リストにない脆弱性パターンが見つかるたびにここに蓄積されます — サンプルデータは一切ありません。",
    detectorProposalsSeenTimes: "{n}回検出",
    detectorProposalsSpottedIn: "検出元",

    landingTitleLine1: "証明できる",
    landingTitleLine1Accent: "攻撃。",
    landingTitleLine2: "信頼できる",
    landingTitleLine2Accent: "修正。",
    landingSubtitle:
      "KAGUTSUCHIは静的ルールとAIスキャンで脆弱性を発見し、隔離されたサンドボックス内で実際にコードを攻撃して証明します。そして同じ方法で — もう一度攻撃して — 修正を証明します。推測も、台本通りのデモもありません。",
    landingCtaScan: "> スキャンを実行",
    landingCtaDashboard: "> 検証記録を見る",
    landingStat1Value: "5",
    landingStat1Label: "脆弱性クラス",
    landingStat2Value: "2",
    landingStat2Label: "検出エンジン",
    landingStat3Value: "100%",
    landingStat3Label: "サンドボックス実行",
    landingStat4Value: "0",
    landingStat4Label: "未検証の判定",
    nameEyebrow: "名前の由来",
    nameTitle: "なぜ「カグツチ」なのか",
    nameBodyPart1:
      "カグツチ（迦具土）は日本神話に登場する火の神です。その誕生の炎は母を焼き死なせるほど激しく、後に父の手によって、悲しみと怒りの中で斬られました。この物語における火は決して穏やかなものではありません — 刀を鍛える力であると同時に、不用意に触れたものを焼き尽くす力でもあるのです。",
    nameBodyPart2:
      "この二面性こそ、私たちがこの名前を選んだ理由です。本エンジンはコードが安全かどうかを推測しません — 実際に火の中に投げ込みます。実際のコードに対する、実際の攻撃です。その火に耐えたものだけが検証済みとなります。耐えられなかったものは、そもそも安全ではなかったのです。",
    nameBodyPart3:
      "提案された修正も、まったく同じペイロードで再びその火にさらされます。「修正確認」がここで意味するのはただ一つ — もう一度攻撃し、今度は耐えたということです。",
    featuresEyebrow: "実際に何をするか",
    featuresTitle: "すべての層が本物であり、模擬ではない。",
    featuresSubtitle: "静的ルールとAIスキャンが候補を洗い出します。実際に起きたことを確認するまで、何も信用されません。",
    feature1Kanji: "検",
    feature1Title: "2つの検出エンジン",
    feature1Body:
      "決定論的スキャナーは既知の危険な呼び出しパターンに一致するものを検出し、AIパスはコードの意味を読み取り、固定リストがまだ知らないクラス — コマンドインジェクション、SQLインジェクション、安全でないデシリアライゼーション、パストラバーサル、安全でないアーカイブ展開など — を捉えます。",
    feature2Kanji: "攻",
    feature2Title: "実際のサンドボックス攻撃",
    feature2Body:
      "すべての検出結果に対して、隔離されたネットワーク遮断済みのサンドボックスで実際の攻撃が試みられます。実際に観測可能な侵害の証拠が作られなければ、それは誤検知としてマークされます — 判定を装った勘ではありません。",
    feature3Kanji: "治",
    feature3Title: "推測ではなく検証された修正",
    feature3Body:
      "提案された修正は、修正済みと呼ばれる前に、まったく同じペイロードで攻撃されます。「修正確認」とは、修正に対して再び攻撃を試み、それが失敗したという意味です — 主張ではなく、結果です。",
    feature4Kanji: "拡",
    feature4Title: "検出リストは拡大し続ける",
    feature4Body:
      "AIが既知のリストにない脆弱性パターンを発見すると、それは「新規クラス」として人間のレビュー待ちになります — 自動的に信頼されることはありませんが、静かに見逃されることもありません。",
    flowEyebrow: "パイプライン",
    flowTitle: "リポジトリのURLから、証明された判定へ。",
    flowSubtitle: "スキャン → 仮説生成 → 攻撃 → 修正 → 検証。",
    flowStep1: "公開GitHubリポジトリのURLを貼り付けると、決定論的スキャナーとAIパスの両方が実際の脆弱性を探します。",
    flowStep2: "検出結果を選択すると、そのコードに特化した攻撃ペイロードが生成されます — 汎用テンプレートではありません。",
    flowStep3: "ペイロードは隔離されたサンドボックス内で実際に実行されます — 結果は主張ではなく観測されたものです。",
    flowStep4: "攻撃が成功した場合、修正が提案され、同じペイロードで再び攻撃されます — 判定は実際に起きたことがすべてです。",
    landingFooterTitle: "リポジトリを貼り付けて、実際に見てみましょう。",
    landingFooterCta: "> スキャンを実行",
  },
};
