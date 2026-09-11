"use client";

import { useState } from "react";
import { SiteNav } from "@/components/SiteNav";

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

interface RepoResult {
  owner: string;
  repo: string;
  files_scanned: number;
  findings: SecurityFinding[];
  sources: Record<string, string>;
  truncated: boolean;
  commit_sha?: string;
}

interface VerifyResult {
  hypothesis: { payload: string };
  before: { exit_code: number; filesystem_diff: { created?: string[] } };
  fixed_source: string | null;
  after: { filesystem_diff: { created?: string[] } } | null;
  result: { verdict: string; summary: string } | null;
  fix_error: string | null;
}

const SEVERITY_COLOR: Record<string, string> = {
  high: "text-rose-400 border-rose-900",
  medium: "text-amber-400 border-amber-900",
  low: "text-slate-400 border-slate-700",
};

function apiUrl(path: string) {
  return `/api/backend${path}`;
}

async function pollJob(jobId: string, owner?: string, repo?: string, sha?: string | null): Promise<RepoResult> {
  const params = new URLSearchParams();
  if (owner) params.set("owner", owner);
  if (repo) params.set("repo", repo);
  if (sha) params.set("sha", sha);

  for (let i = 0; i < 240; i++) {
    await new Promise((r) => setTimeout(r, 2000));
    const res = await fetch(apiUrl(`/analyze-repo/jobs/${jobId}?${params.toString()}`));
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `Request failed (${res.status})`);
    }
    const body = await res.json();
    if (body.status === "error") throw new Error(body.error ?? "Scan failed");
    if (body.status === "done") return body.result as RepoResult;
  }
  throw new Error("This scan is taking unusually long — try again shortly.");
}

function FindingCard({ finding, source, repoOwner, repoName }: { finding: SecurityFinding; source: string | undefined; repoOwner: string; repoName: string }) {
  const [open, setOpen] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
  const [showPrForm, setShowPrForm] = useState(false);
  const [token, setToken] = useState("");
  const [openingPr, setOpeningPr] = useState(false);
  const [prError, setPrError] = useState<string | null>(null);
  const [prUrl, setPrUrl] = useState<string | null>(null);

  async function runVerify() {
    if (!source) return;
    setVerifying(true);
    setVerifyError(null);
    try {
      const res = await fetch(apiUrl("/verify"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, finding }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
      setVerifyResult(body);
    } catch (err) {
      setVerifyError(err instanceof Error ? err.message : String(err));
    } finally {
      setVerifying(false);
    }
  }

  async function openPr() {
    if (!source || !verifyResult?.fixed_source || !token.trim()) return;
    setOpeningPr(true);
    setPrError(null);
    try {
      const res = await fetch(apiUrl("/open-pr"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_url: `https://github.com/${repoOwner}/${repoName}`,
          file_path: finding.file_path,
          symbol: finding.symbol,
          original_source: source,
          fixed_function_source: verifyResult.fixed_source,
          finding_summary: finding.rationale,
          github_token: token,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
      setPrUrl(body.pr_url);
      setToken("");
    } catch (err) {
      setPrError(err instanceof Error ? err.message : String(err));
    } finally {
      setOpeningPr(false);
    }
  }

  return (
    <div className="rounded border border-slate-800 bg-slate-900/40">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-slate-900/70"
      >
        <div className="flex items-center gap-3 overflow-hidden">
          <span className="shrink-0 font-mono text-xs text-slate-500">{finding.sensitive_op}</span>
          <span className="truncate text-sm text-slate-300">{finding.file_path}</span>
        </div>
        <span className={`shrink-0 rounded border px-2 py-0.5 font-mono text-[10px] uppercase ${SEVERITY_COLOR[finding.severity_hint] ?? SEVERITY_COLOR.low}`}>
          {finding.severity_hint}
        </span>
      </button>

      {open && (
        <div className="space-y-4 border-t border-slate-800 p-4">
          <p className="text-sm text-slate-400">{finding.rationale}</p>
          <pre className="max-h-56 overflow-auto rounded bg-slate-950 p-3 font-mono text-xs text-slate-400">{finding.diff_hunk}</pre>

          {!verifyResult && (
            <button
              onClick={runVerify}
              disabled={verifying || !source}
              className="rounded bg-white px-4 py-2 text-xs font-semibold text-slate-950 disabled:opacity-50"
            >
              {verifying ? "Attacking…" : "Attack & Verify"}
            </button>
          )}
          {verifyError && <p className="rounded border border-rose-900 bg-rose-950/40 p-3 text-xs text-rose-300">{verifyError}</p>}

          {verifyResult && (
            <div className="space-y-3 border-t border-slate-800 pt-4">
              <p className="text-sm text-slate-300">{verifyResult.result?.summary ?? "This finding was a false positive."}</p>
              <div className="font-mono text-xs text-slate-500">
                payload: <span className="text-slate-300">{verifyResult.hypothesis.payload}</span>
              </div>
              {verifyResult.fixed_source && (
                <>
                  <div className="font-mono text-[10px] tracking-wide text-emerald-400 uppercase">Proposed fix</div>
                  <pre className="max-h-56 overflow-auto rounded border border-emerald-900 bg-slate-950 p-3 font-mono text-xs text-emerald-300">
                    {verifyResult.fixed_source}
                  </pre>

                  {verifyResult.result?.verdict === "VERIFIED_FIXED" &&
                    (prUrl ? (
                      <a href={prUrl} target="_blank" rel="noreferrer" className="inline-block rounded bg-emerald-600 px-4 py-2 text-xs font-semibold text-white">
                        Pull request opened ↗
                      </a>
                    ) : showPrForm ? (
                      <div className="space-y-2 rounded border border-slate-800 bg-slate-950 p-3">
                        <p className="text-[11px] text-slate-500">
                          Uses a GitHub token with repo write access, sent directly to GitHub for this one request — never stored.
                        </p>
                        <input
                          type="password"
                          value={token}
                          onChange={(e) => setToken(e.target.value)}
                          placeholder="GitHub personal access token (repo scope)"
                          className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-1.5 font-mono text-xs text-slate-200 outline-none"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={openPr}
                            disabled={openingPr || !token.trim()}
                            className="rounded bg-white px-3 py-1.5 text-xs font-semibold text-slate-950 disabled:opacity-50"
                          >
                            {openingPr ? "Opening…" : "Create pull request"}
                          </button>
                          <button onClick={() => setShowPrForm(false)} className="rounded border border-slate-700 px-3 py-1.5 text-xs text-slate-300">
                            Cancel
                          </button>
                        </div>
                        {prError && <p className="rounded border border-rose-900 bg-rose-950/40 p-2 text-[11px] text-rose-300">{prError}</p>}
                      </div>
                    ) : (
                      <button onClick={() => setShowPrForm(true)} className="rounded border border-emerald-700 px-4 py-2 text-xs font-semibold text-emerald-400">
                        Open a PR with this fix
                      </button>
                    ))}
                </>
              )}
              {verifyResult.fix_error && <p className="text-xs text-slate-500">Fix not available: {verifyResult.fix_error}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const EXAMPLES = [
  { label: "PyGoat", url: "https://github.com/adeyosemanputra/pygoat" },
  { label: "Flask", url: "https://github.com/pallets/flask" },
];

export default function ScanPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RepoResult | null>(null);

  async function handleSubmit(e?: React.FormEvent, overrideUrl?: string) {
    e?.preventDefault();
    const target = (overrideUrl ?? repoUrl).trim();
    if (!target || loading) return;
    setLoading(true);
    setPolling(false);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(apiUrl("/analyze-repo/start"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: target }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
      if (body.cached && body.result) {
        setResult({ ...body.result, commit_sha: body.commit_sha });
        return;
      }
      if (!body.job_id) throw new Error("Unexpected response starting the scan.");
      setPolling(true);
      const r = await pollJob(body.job_id, body.owner, body.repo, body.commit_sha);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      setPolling(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <SiteNav />

        <h1 className="text-3xl font-bold sm:text-4xl">Scan a public repo</h1>
        <p className="mt-2 max-w-lg text-slate-400">
          Paste a GitHub URL. Real static analysis, then a real sandboxed exploit, then a real proposed fix.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-3 sm:flex-row">
          <input
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="flex-1 rounded border border-slate-700 bg-slate-900 px-4 py-3 font-mono text-sm text-slate-100 outline-none focus:border-slate-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-white px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50"
          >
            {loading ? "Scanning…" : "Analyze"}
          </button>
        </form>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span>Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex.url}
              disabled={loading}
              onClick={() => {
                setRepoUrl(ex.url);
                handleSubmit(undefined, ex.url);
              }}
              className="rounded border border-slate-700 px-2 py-1 hover:border-slate-500 disabled:opacity-50"
            >
              {ex.label}
            </button>
          ))}
        </div>

        {polling && <p className="mt-6 text-sm text-slate-500">Still scanning — larger repos can take a minute or two.</p>}
        {error && <p className="mt-6 rounded border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-300">{error}</p>}

        {result && (
          <div className="mt-12">
            <div className="mb-6 grid grid-cols-2 gap-px overflow-hidden rounded border border-slate-800 bg-slate-800 sm:grid-cols-2">
              <div className="bg-slate-950 p-4">
                <div className="text-3xl font-bold">{result.files_scanned}</div>
                <div className="text-xs text-slate-500 uppercase">Files scanned</div>
              </div>
              <div className="bg-slate-950 p-4">
                <div className="text-3xl font-bold">{result.findings.length}</div>
                <div className="text-xs text-slate-500 uppercase">Findings</div>
              </div>
            </div>

            {result.findings.length === 0 ? (
              <p className="rounded border border-dashed border-slate-800 p-8 text-center text-slate-400">
                No findings — nothing in this repo matched a known vulnerability pattern.
              </p>
            ) : (
              <div className="space-y-2">
                {result.findings.map((f) => (
                  <FindingCard key={f.finding_id} finding={f} source={result.sources[f.file_path]} repoOwner={result.owner} repoName={result.repo} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
