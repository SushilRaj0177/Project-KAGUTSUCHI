"use client";

import { useState } from "react";
import { signIn, useSession } from "next-auth/react";
import { SEVERITY_COLOR, type SecurityFinding, type VerifyResult } from "@/lib/scanTypes";

function apiUrl(path: string) {
  return `/api/backend${path}`;
}

export function FindingCard({
  finding,
  source,
  repoOwner,
  repoName,
}: {
  finding: SecurityFinding;
  source: string | undefined;
  repoOwner: string;
  repoName: string;
}) {
  const { data: session } = useSession();
  const signedIn = Boolean(session?.user);
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
    if (!source || !verifyResult?.fixed_source) return;
    if (!signedIn && !token.trim()) return;
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
          // Ignored server-side and replaced with the real OAuth token
          // when signed in - see app/api/backend/open-pr/route.ts.
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
        <span
          className={`shrink-0 rounded border px-2 py-0.5 font-mono text-[10px] uppercase ${
            SEVERITY_COLOR[finding.severity_hint] ?? SEVERITY_COLOR.low
          }`}
        >
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
              {verifying ? "Attacking…" : source ? "Attack & Verify" : "Source unavailable"}
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
                        {signedIn ? (
                          <p className="text-[11px] text-slate-500">Opens the PR as your signed-in GitHub account.</p>
                        ) : (
                          <>
                            <p className="text-[11px] text-slate-500">
                              Uses a GitHub token with repo write access, sent directly to GitHub for this one
                              request — never stored.{" "}
                              <button
                                type="button"
                                onClick={() => signIn("github")}
                                className="underline hover:text-slate-300"
                              >
                                Sign in with GitHub
                              </button>{" "}
                              instead to skip pasting a token.
                            </p>
                            <input
                              type="password"
                              value={token}
                              onChange={(e) => setToken(e.target.value)}
                              placeholder="GitHub personal access token (repo scope)"
                              className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-1.5 font-mono text-xs text-slate-200 outline-none"
                            />
                          </>
                        )}
                        <div className="flex gap-2">
                          <button
                            onClick={openPr}
                            disabled={openingPr || (!signedIn && !token.trim())}
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
