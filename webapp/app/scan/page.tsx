"use client";

import { useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import { FindingCard } from "@/components/FindingCard";
import type { RepoResult } from "@/lib/scanTypes";

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

function ShareLinks({ owner, repo, sha }: { owner: string; repo: string; sha: string }) {
  const [copied, setCopied] = useState<"link" | "badge" | null>(null);
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const permalink = `${origin}/scan/${owner}/${repo}/${sha}`;
  const badgeMarkdown = `[![kagutsuchi](${origin}/api/badge/${owner}/${repo})](${permalink})`;

  async function copy(text: string, which: "link" | "badge") {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(which);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      // clipboard access denied — nothing to do, the text is still selectable.
    }
  }

  return (
    <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-slate-800 pt-6 text-xs text-slate-500">
      <span>Share this result:</span>
      <button onClick={() => copy(permalink, "link")} className="rounded border border-slate-700 px-3 py-1.5 hover:border-slate-500">
        {copied === "link" ? "Copied!" : "Copy permalink"}
      </button>
      <button onClick={() => copy(badgeMarkdown, "badge")} className="rounded border border-slate-700 px-3 py-1.5 hover:border-slate-500">
        {copied === "badge" ? "Copied!" : "Copy README badge"}
      </button>
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

            {result.commit_sha && <ShareLinks owner={result.owner} repo={result.repo} sha={result.commit_sha} />}
          </div>
        )}
      </div>
    </main>
  );
}
