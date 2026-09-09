"use client";

import { useState } from "react";
import { GridFloor } from "./GridFloor";
import { MagneticButton } from "./MagneticButton";
import { Marquee } from "./Marquee";
import { Particles } from "./Particles";
import { useLanguage } from "./LanguageContext";
import { useInView } from "./useInView";

interface SecurityFinding {
  finding_id: string;
  file_path: string;
  symbol: string;
  diff_hunk: string;
  sensitive_op: string;
  rationale: string;
  detected_by: string;
  severity_hint: "low" | "medium" | "high";
}

interface RepoAnalyzeResponse {
  owner: string;
  repo: string;
  files_scanned: number;
  findings: SecurityFinding[];
  sources: Record<string, string>;
}

interface VerifyResponse {
  hypothesis: { payload: string; security_property: string };
  before: { exit_code: number; filesystem_diff: { created?: string[] } };
  fixed_source: string | null;
  after: { exit_code: number; filesystem_diff: { created?: string[] } } | null;
  result: { verdict: string; summary: string } | null;
  fix_error: string | null;
}

const SEVERITY_MARK: Record<string, string> = { high: "●●●", medium: "●●○", low: "●○○" };

// Calls our own Next.js API routes (app/api/backend/*), which proxy to the
// FastAPI backend server-side -- the browser never talks to the backend
// directly, so no cross-origin/CORS issue exists (see the proxy routes'
// comments for why a direct browser call doesn't work with the Codespaces
// backend).
function apiUrl(path: string): string {
  return `/api/backend${path}`;
}

function FindingCard({
  finding,
  source,
  index,
}: {
  finding: SecurityFinding;
  source: string | undefined;
  index: number;
}) {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const { ref, inView } = useInView<HTMLDivElement>();
  const [open, setOpen] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);

  async function runVerify() {
    if (!source) return;
    setVerifying(true);
    setVerifyError(null);
    setVerifyResult(null);
    try {
      const res = await fetch(apiUrl("/verify"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, finding }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Request failed (${res.status})`);
      }
      setVerifyResult(await res.json());
    } catch (err) {
      setVerifyError(err instanceof Error ? err.message : String(err));
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div
      ref={ref}
      className={`hover-lift border border-line bg-void-900/60 ${inView ? "in-view" : "scroll-hidden"}`}
      style={{ transitionDelay: inView ? `${index * 60}ms` : "0ms" }}
    >
      <button
        data-cursor="hover"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left hover:bg-void-850"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span className={`font-display text-base font-bold ${jp}`}>{t.vulnClass[finding.sensitive_op] ?? finding.sensitive_op}</span>
          <span className="font-mono text-xs text-steel-400">{finding.file_path}</span>
        </div>
        <span
          className={`font-mono text-xs tracking-widest ${finding.severity_hint === "high" ? "neon-text-pink" : "text-paper-50"}`}
          title={finding.severity_hint}
        >
          {SEVERITY_MARK[finding.severity_hint] ?? SEVERITY_MARK.low}
        </span>
      </button>

      {open && (
        <div className="fade-in-up space-y-4 border-t border-line p-5">
          <div>
            <div className={`text-xs font-bold tracking-wide neon-text-cyan uppercase ${jp}`}>{t.rationale}</div>
            <p className="mt-2 text-sm leading-relaxed text-paper-50">{finding.rationale}</p>
          </div>

          <div>
            <div className={`bracket-label mb-2 font-mono text-xs font-bold text-steel-400 uppercase ${jp}`}>
              {t.vulnerableCode}
            </div>
            <div className="mb-2 flex flex-wrap gap-2">
              <span className="font-mono text-xs text-steel-400">{finding.symbol}()</span>
              <span className="border border-line-strong px-2 py-0.5 font-mono text-[11px] uppercase text-steel-400">
                [ {finding.sensitive_op} ]
              </span>
            </div>
            <pre className="max-h-56 overflow-auto border border-line bg-void-950 p-3 font-mono text-xs text-steel-400">
              {finding.diff_hunk}
            </pre>
          </div>

          <MagneticButton
            onClick={runVerify}
            disabled={verifying || !source}
            className={`border px-4 py-2 text-xs font-bold uppercase tracking-wide transition-colors ${jp} ${
              verifying
                ? "cursor-wait border-line-strong text-steel-400"
                : "neon-border-pink border-neon-pink text-neon-pink-soft hover:bg-neon-pink/10"
            }`}
          >
            {verifying ? t.verifyingButton : t.verifyButton}
          </MagneticButton>

          {verifyError && (
            <p className="border border-neon-pink/40 bg-neon-pink/10 p-3 font-mono text-xs text-neon-pink-soft">{verifyError}</p>
          )}

          {verifyResult && (
            <div className="fade-in-up space-y-4 border-t border-line pt-4">
              <div>
                <div className={`text-xs font-bold tracking-wide neon-text-cyan uppercase ${jp}`}>{t.whatHappened}</div>
                {verifyResult.result ? (
                  <p className="mt-2 text-sm leading-relaxed text-paper-50">{verifyResult.result.summary}</p>
                ) : (
                  <p className="mt-2 text-sm leading-relaxed text-paper-50">
                    {verifyResult.before.filesystem_diff?.created?.includes("/tmp/kagutsuchi_pwned")
                      ? t.plainOther
                      : t.noFindingsBody}
                  </p>
                )}
              </div>

              <div>
                <div className={`bracket-label mb-2 font-mono text-xs font-bold text-steel-400 uppercase ${jp}`}>
                  {t.technicalDetails}
                </div>
                <div className={`text-xs font-bold uppercase text-steel-400 ${jp}`}>{t.attackResult}</div>
                <div className="mt-1 inline-block border border-line bg-void-950 px-2 py-1 font-mono text-xs text-paper-50">
                  {verifyResult.hypothesis.payload}
                </div>
                <div className="mt-2 grid gap-3 md:grid-cols-2">
                  <EvidenceBox label={t.before} evidence={verifyResult.before} tone="pink" />
                  {verifyResult.after && <EvidenceBox label={t.after} evidence={verifyResult.after} tone="cyan" />}
                </div>

                {verifyResult.fixed_source ? (
                  <div className="mt-4">
                    <div className={`text-xs font-bold uppercase neon-text-cyan ${jp}`}>{t.proposedFix}</div>
                    <pre className="mt-1 max-h-56 overflow-auto border border-neon-cyan/30 bg-void-950 p-3 font-mono text-xs text-neon-cyan-soft">
                      {verifyResult.fixed_source}
                    </pre>
                  </div>
                ) : (
                  verifyResult.fix_error && (
                    <p className="mt-4 border border-line bg-void-950 p-3 text-xs text-steel-400">
                      <span className={`font-bold text-paper-50 ${jp}`}>{t.fixUnavailable}: </span>
                      {verifyResult.fix_error}
                    </p>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function EvidenceBox({
  label,
  evidence,
  tone,
}: {
  label: string;
  evidence: { exit_code: number; filesystem_diff: { created?: string[] } };
  tone: "pink" | "cyan";
}) {
  const { t } = useLanguage();
  const marker = evidence.filesystem_diff?.created?.includes("/tmp/kagutsuchi_pwned");
  const border = tone === "pink" ? "border-t-neon-pink" : "border-t-neon-cyan";
  const text = tone === "pink" ? "neon-text-pink" : "neon-text-cyan";
  return (
    <div className={`border border-line ${border} border-t-2 bg-void-950 p-3 text-xs`}>
      <div className={`font-bold ${text}`}>{label}</div>
      <div className="mt-2 flex justify-between text-steel-400">
        <span>{t.exitCode}</span>
        <span className="font-mono text-paper-50">{evidence.exit_code}</span>
      </div>
      <div className="mt-1 flex justify-between text-steel-400">
        <span>{t.markerCreated}</span>
        <span className="font-mono text-paper-50">{marker ? "kagutsuchi_pwned" : t.none}</span>
      </div>
    </div>
  );
}

export function RepoScanner() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RepoAnalyzeResponse | null>(null);
  const { ref: resultsRef, inView: resultsInView } = useInView<HTMLDivElement>();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(apiUrl("/analyze-repo"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Request failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <section className="relative flex min-h-[78vh] flex-col items-center justify-center overflow-hidden text-center">
        <Particles />
        <GridFloor />

        <div className={`relative z-10 font-mono text-xs tracking-[0.35em] neon-text-cyan uppercase ${jp}`}>
          {t.heroKanji}
        </div>

        <h2
          data-text={t.heroTitle}
          className="glitch-wrap font-display relative z-10 mt-6 max-w-4xl text-6xl leading-[0.95] font-extrabold tracking-tight text-paper-50 md:text-8xl"
        >
          {t.heroTitle}
        </h2>

        <p className={`relative z-10 mt-6 max-w-lg text-sm leading-relaxed text-steel-400 ${jp}`}>
          {t.heroSubtitle}
        </p>

        <form onSubmit={handleSubmit} className="hud-frame relative z-10 mt-10 w-full max-w-xl border border-line-strong bg-void-900/70 p-4 backdrop-blur-sm">
          <div className="mb-3 flex items-center gap-2 border-b border-line pb-2 font-mono text-[10px] tracking-widest text-steel-400 uppercase">
            <span className="h-2 w-2 rounded-full bg-neon-pink shadow-[0_0_6px_var(--neon-pink)]" />
            <span>SYSTEM://SCAN.EXE</span>
          </div>
          <label className="flex items-center gap-2">
            <span className="neon-text-cyan font-mono cursor-blink">&gt;</span>
            <input
              data-cursor="hover"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder={t.repoPlaceholder}
              className="flex-1 bg-transparent font-mono text-sm text-paper-50 outline-none placeholder:text-steel-600"
            />
          </label>
          <MagneticButton
            type="submit"
            disabled={loading}
            className={`neon-border-pink mt-4 w-full border border-neon-pink bg-neon-pink/10 px-6 py-2.5 text-xs font-bold tracking-[0.2em] text-neon-pink-soft uppercase transition-colors hover:bg-neon-pink/25 disabled:cursor-wait disabled:opacity-50 ${jp}`}
          >
            {loading ? t.scanningButton : t.scanButton}
          </MagneticButton>
        </form>

        {error && (
          <p className="relative z-10 mt-4 max-w-md border border-neon-pink/40 bg-neon-pink/10 p-3 font-mono text-xs text-neon-pink-soft">
            {error}
          </p>
        )}
      </section>

      <Marquee text={`${t.heroTitle.replace(/\.$/, "")} — `} />

      {result && (
        <section ref={resultsRef} className="mt-10 border-t border-line pt-10">
          <div
            className={`mb-8 grid grid-cols-2 gap-px overflow-hidden border border-line bg-line ${resultsInView ? "in-view" : "scroll-hidden"}`}
          >
            <StatTile label={t.filesScanned} value={result.files_scanned} tone="cyan" />
            <StatTile label={t.findingsCount} value={result.findings.length} tone="pink" />
          </div>

          {result.findings.length === 0 ? (
            <div className="border border-dashed border-line-strong px-8 py-16 text-center">
              <h3 className={`font-display text-2xl font-extrabold ${jp}`}>{t.noFindings}</h3>
              <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.noFindingsBody}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {result.findings.map((finding, i) => (
                <FindingCard
                  key={finding.finding_id}
                  finding={finding}
                  source={result.sources[finding.file_path]}
                  index={i}
                />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function StatTile({ label, value, tone }: { label: string; value: number; tone: "cyan" | "pink" }) {
  const { lang } = useLanguage();
  const border = tone === "cyan" ? "border-t-neon-cyan" : "border-t-neon-pink";
  return (
    <div className={`border-t-2 bg-void-900 p-5 ${border}`}>
      <div className={`text-[11px] uppercase tracking-wide text-steel-400 ${lang === "ja" ? "font-jp normal-case" : ""}`}>
        {label}
      </div>
      <div className="font-display text-4xl font-extrabold tabular-nums text-paper-50">{value}</div>
    </div>
  );
}
