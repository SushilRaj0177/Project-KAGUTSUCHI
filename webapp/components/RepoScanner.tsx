"use client";

import { useState } from "react";
import { MagneticButton } from "./MagneticButton";
import { Marquee } from "./Marquee";
import { RevealText } from "./RevealText";
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

// Severity reads through weight and symbol, never color.
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
      className={`hover-lift border border-line ${inView ? "in-view" : "scroll-hidden"}`}
      style={{ transitionDelay: inView ? `${index * 60}ms` : "0ms" }}
    >
      <button
        data-cursor="hover"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left hover:bg-ink-900"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-sm text-paper-50">{finding.file_path}</span>
          <span className="font-mono text-xs text-steel-400">{finding.symbol}()</span>
          <span className="border border-line-strong px-2 py-0.5 font-mono text-[11px] uppercase text-steel-400">
            [ {finding.sensitive_op} ]
          </span>
        </div>
        <span
          className={`font-mono text-xs tracking-widest ${finding.severity_hint === "high" ? "text-seal-500" : "text-paper-50"}`}
          title={finding.severity_hint}
        >
          {SEVERITY_MARK[finding.severity_hint] ?? SEVERITY_MARK.low}
        </span>
      </button>

      {open && (
        <div className="fade-in-up space-y-4 border-t border-line p-5">
          <div>
            <div className={`bracket-label font-mono text-xs font-bold uppercase text-steel-400 ${jp}`}>{t.rationale}</div>
            <p className="mt-1 text-sm text-paper-50">{finding.rationale}</p>
          </div>
          <pre className="max-h-56 overflow-auto border border-line bg-ink-900 p-3 font-mono text-xs text-steel-400">
            {finding.diff_hunk}
          </pre>

          <MagneticButton
            onClick={runVerify}
            disabled={verifying || !source}
            className={`border px-4 py-2 text-xs font-bold uppercase tracking-wide transition-colors ${jp} ${
              verifying
                ? "cursor-wait border-line-strong text-steel-400"
                : "border-paper-50 text-paper-50 hover:bg-paper-50 hover:text-ink-950"
            }`}
          >
            {verifying ? t.verifyingButton : t.verifyButton}
          </MagneticButton>

          {verifyError && (
            <p className="border border-line-strong p-3 font-mono text-xs text-paper-50">{verifyError}</p>
          )}

          {verifyResult && (
            <div className="fade-in-up space-y-3 border-t border-line pt-4">
              <div>
                <div className={`text-xs font-bold uppercase text-steel-400 ${jp}`}>
                  {t.attackResult}
                </div>
                <div className="mt-1 inline-block border border-line bg-ink-900 px-2 py-1 font-mono text-xs text-paper-50">
                  {verifyResult.hypothesis.payload}
                </div>
                <div className="mt-2 grid gap-3 md:grid-cols-2">
                  <EvidenceBox label={t.before} evidence={verifyResult.before} />
                  {verifyResult.after && <EvidenceBox label={t.after} evidence={verifyResult.after} />}
                </div>
              </div>

              {verifyResult.result && (
                <p className="border border-line-strong bg-ink-900 p-3 text-sm text-paper-50">
                  {verifyResult.result.summary}
                </p>
              )}

              {verifyResult.fixed_source ? (
                <div>
                  <div className={`text-xs font-bold uppercase text-paper-50 ${jp}`}>{t.proposedFix}</div>
                  <pre className="mt-1 max-h-56 overflow-auto border border-line-strong bg-ink-900 p-3 font-mono text-xs text-paper-50">
                    {verifyResult.fixed_source}
                  </pre>
                </div>
              ) : (
                verifyResult.fix_error && (
                  <p className="border border-line bg-ink-900 p-3 text-xs text-steel-400">
                    <span className={`font-bold text-paper-50 ${jp}`}>{t.fixUnavailable}: </span>
                    {verifyResult.fix_error}
                  </p>
                )
              )}
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
}: {
  label: string;
  evidence: { exit_code: number; filesystem_diff: { created?: string[] } };
}) {
  const { t } = useLanguage();
  const marker = evidence.filesystem_diff?.created?.includes("/tmp/kagutsuchi_pwned");
  return (
    <div className="border border-line bg-ink-900 p-3 text-xs">
      <div className="font-bold text-paper-50">{label}</div>
      <div className="mt-2 flex justify-between text-steel-400">
        <span>{t.exitCode}</span>
        <span className="font-mono">{evidence.exit_code}</span>
      </div>
      <div className="mt-1 flex justify-between text-steel-400">
        <span>{t.markerCreated}</span>
        <span className="font-mono">{marker ? "kagutsuchi_pwned" : t.none}</span>
      </div>
    </div>
  );
}

export function RepoScanner() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [repoUrl, setRepoUrl] = useState("");
  const [focused, setFocused] = useState(false);
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
      <section className="relative overflow-hidden pb-4">
        {/* The seal: a big pulsing red disc, half-cropped off the edge for scale/energy */}
        <div
          className="seal-pulse pointer-events-none absolute top-1/2 -right-40 h-[520px] w-[520px] -translate-y-1/2 rounded-full bg-seal-500"
          style={{ filter: "blur(2px)" }}
        />
        <div
          className="pointer-events-none absolute top-1/2 -right-24 h-[380px] w-[380px] -translate-y-1/2 rounded-full border border-paper-50/30"
          style={{ animation: "spin 30s linear infinite" }}
        />

        {/* Vertical Japanese strip along the right edge */}
        <div className="vertical-text font-jp pointer-events-none absolute top-0 right-6 hidden h-full py-6 text-sm tracking-[0.3em] text-paper-50/50 md:block">
          自律型セキュリティ検証エンジン
        </div>

        <div className="relative z-10 max-w-2xl">
          <div
            className={`fade-in-up text-xs tracking-[0.25em] text-steel-400 uppercase ${jp}`}
            style={{ animationDelay: "0.1s", opacity: 0 }}
          >
            {t.heroKanji}
          </div>
          <h2
            className="parallax-slow font-display mt-4 text-6xl leading-[0.95] font-extrabold tracking-tight md:text-7xl"
          >
            <RevealText text={t.heroTitle} startDelay={0.15} />
          </h2>
          <p
            className={`fade-in-up mt-6 max-w-md text-sm leading-relaxed text-steel-400 ${jp}`}
            style={{ animationDelay: "0.6s", opacity: 0 }}
          >
            {t.heroSubtitle}
          </p>

          <form
            onSubmit={handleSubmit}
            className="fade-in-up mt-10 max-w-xl"
            style={{ animationDelay: "0.75s", opacity: 0 }}
          >
            <label className="relative flex items-center gap-2 border-b border-line-strong pb-2">
              <span className="font-mono text-seal-500">&gt;</span>
              <input
                data-cursor="hover"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder={t.repoPlaceholder}
                className="flex-1 bg-transparent font-mono text-sm text-paper-50 outline-none placeholder:text-steel-600"
              />
              <span
                className="absolute right-0 -bottom-px left-0 h-px origin-center bg-seal-500 transition-transform duration-300"
                style={{ transform: focused ? "scaleX(1)" : "scaleX(0)" }}
              />
            </label>
            <MagneticButton
              type="submit"
              disabled={loading}
              className={`mt-5 border-2 border-seal-500 bg-seal-500 px-6 py-2.5 text-xs font-bold tracking-[0.2em] text-ink-950 uppercase transition-colors hover:bg-transparent hover:text-seal-400 disabled:cursor-wait disabled:opacity-50 ${jp}`}
            >
              {loading ? t.scanningButton : t.scanButton}
            </MagneticButton>
          </form>

          {error && <p className="mt-4 max-w-md border border-line-strong p-3 font-mono text-xs text-paper-50">{error}</p>}
        </div>
      </section>

      <Marquee text={`${t.heroTitle.replace(/\.$/, "")} — `} />

      {result && (
        <section ref={resultsRef} className="border-t border-line pt-10">
          <div
            className={`mb-8 grid grid-cols-2 gap-px overflow-hidden border border-line bg-line ${resultsInView ? "in-view" : "scroll-hidden"}`}
          >
            <StatTile label={t.filesScanned} value={result.files_scanned} />
            <StatTile label={t.findingsCount} value={result.findings.length} />
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

function StatTile({ label, value }: { label: string; value: number }) {
  const { lang } = useLanguage();
  return (
    <div className="border-t-2 border-paper-50 p-5">
      <div className={`text-[11px] uppercase tracking-wide text-steel-400 ${lang === "ja" ? "font-jp normal-case" : ""}`}>
        {label}
      </div>
      <div className="font-display text-4xl font-extrabold tabular-nums text-paper-50">{value}</div>
    </div>
  );
}
