"use client";

import { useState } from "react";
import Link from "next/link";

interface Finding {
  finding_id: string;
  file_path: string;
  symbol: string;
  sensitive_op: string;
  severity_hint: string;
  rationale: string;
}

interface CompareResult {
  base_ref: string;
  head_ref: string;
  base_files_scanned: number;
  head_files_scanned: number;
  added: Finding[];
  removed: Finding[];
  unchanged_count: number;
  detail?: string;
}

export default function ComparePage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [baseRef, setBaseRef] = useState("main");
  const [headRef, setHeadRef] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim() || !baseRef.trim() || !headRef.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/backend/compare-repo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl.trim(), base_ref: baseRef.trim(), head_ref: headRef.trim() }),
      });
      const body = await res.json();
      if (!res.ok || body.detail) throw new Error(body.detail ?? `Request failed (${res.status})`);
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <nav className="mb-16 flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold tracking-wide">
            KAGUTSUCHI
          </Link>
          <Link href="/scan" className="text-sm text-slate-400 hover:text-white">
            Scan
          </Link>
        </nav>

        <h1 className="text-3xl font-bold sm:text-4xl">Compare two branches</h1>
        <p className="mt-2 max-w-lg text-slate-400">
          Did this branch or PR introduce a new vulnerability — or fix one? Scans both refs and diffs the findings.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-3">
          <input
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="w-full rounded border border-slate-700 bg-slate-900 px-4 py-3 font-mono text-sm text-slate-100 outline-none focus:border-slate-500"
          />
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={baseRef}
              onChange={(e) => setBaseRef(e.target.value)}
              placeholder="base ref (e.g. main)"
              className="flex-1 rounded border border-slate-700 bg-slate-900 px-4 py-3 font-mono text-sm text-slate-100 outline-none focus:border-slate-500"
            />
            <input
              value={headRef}
              onChange={(e) => setHeadRef(e.target.value)}
              placeholder="head ref (e.g. my-branch)"
              className="flex-1 rounded border border-slate-700 bg-slate-900 px-4 py-3 font-mono text-sm text-slate-100 outline-none focus:border-slate-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded bg-white px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50"
            >
              {loading ? "Comparing…" : "Compare"}
            </button>
          </div>
        </form>

        {error && <p className="mt-6 rounded border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-300">{error}</p>}

        {result && (
          <div className="mt-10 space-y-8">
            <div className="grid grid-cols-2 gap-px overflow-hidden rounded border border-slate-800 bg-slate-800">
              <div className="bg-slate-950 p-4">
                <div className="text-2xl font-bold">{result.base_files_scanned}</div>
                <div className="text-xs text-slate-500 uppercase">{result.base_ref} files scanned</div>
              </div>
              <div className="bg-slate-950 p-4">
                <div className="text-2xl font-bold">{result.head_files_scanned}</div>
                <div className="text-xs text-slate-500 uppercase">{result.head_ref} files scanned</div>
              </div>
            </div>

            <div>
              <h2 className="font-mono text-xs tracking-wide text-rose-400 uppercase">
                Added ({result.added.length})
              </h2>
              {result.added.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">No new findings introduced.</p>
              ) : (
                <div className="mt-2 space-y-2">
                  {result.added.map((f) => (
                    <div key={f.finding_id} className="rounded border border-rose-900/50 bg-rose-950/20 p-3">
                      <div className="flex items-center gap-3 font-mono text-xs text-slate-400">
                        <span>{f.sensitive_op}</span>
                        <span className="text-slate-300">{f.file_path}</span>
                      </div>
                      <p className="mt-1 text-sm text-slate-400">{f.rationale}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h2 className="font-mono text-xs tracking-wide text-emerald-400 uppercase">
                Removed ({result.removed.length})
              </h2>
              {result.removed.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">No findings fixed between these refs.</p>
              ) : (
                <div className="mt-2 space-y-2">
                  {result.removed.map((f) => (
                    <div key={f.finding_id} className="rounded border border-emerald-900/50 bg-emerald-950/20 p-3">
                      <div className="flex items-center gap-3 font-mono text-xs text-slate-400">
                        <span>{f.sensitive_op}</span>
                        <span className="text-slate-300">{f.file_path}</span>
                      </div>
                      <p className="mt-1 text-sm text-slate-400">{f.rationale}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <p className="text-xs text-slate-600">{result.unchanged_count} finding(s) unchanged between refs.</p>
          </div>
        )}
      </div>
    </main>
  );
}
