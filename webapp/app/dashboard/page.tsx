"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface RunRow {
  id: string;
  created_at: string;
  fixture_name: string;
  sensitive_op: string;
  verdict: string;
  confidence: number;
  hypothesis_confidence: number | null;
  summary: string;
}

const VERDICT_COLOR: Record<string, string> = {
  VERIFIED_FIXED: "text-emerald-400 border-emerald-900",
  STILL_VULNERABLE: "text-rose-400 border-rose-900",
  FALSE_POSITIVE: "text-slate-400 border-slate-700",
  INCONCLUSIVE: "text-amber-400 border-amber-900",
};

export default function DashboardPage() {
  const [runs, setRuns] = useState<RunRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/runs")
      .then((res) => res.json())
      .then((body) => {
        if (body.detail) setError(body.detail);
        else setRuns(body.runs ?? []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

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

        <h1 className="text-3xl font-bold sm:text-4xl">Live runs</h1>
        <p className="mt-2 max-w-lg text-slate-400">
          Real completed verifications from actual site usage — not sample data.
        </p>

        {error && <p className="mt-6 rounded border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-300">{error}</p>}

        {runs === null && !error && <p className="mt-10 text-sm text-slate-500">Loading…</p>}

        {runs && runs.length === 0 && (
          <p className="mt-10 rounded border border-dashed border-slate-800 p-8 text-center text-slate-400">
            No runs recorded yet. Attack a finding on the <Link href="/scan" className="underline">scan page</Link> to
            create one.
          </p>
        )}

        {runs && runs.length > 0 && (
          <div className="mt-10 space-y-2">
            {runs.map((r) => (
              <div key={r.id} className="rounded border border-slate-800 bg-slate-900/40 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-slate-500">{r.sensitive_op}</span>
                    <span className="text-sm text-slate-300">{r.fixture_name}</span>
                  </div>
                  <span className={`rounded border px-2 py-0.5 font-mono text-[10px] uppercase ${VERDICT_COLOR[r.verdict] ?? "text-slate-400 border-slate-700"}`}>
                    {r.verdict}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-400">{r.summary}</p>
                <div className="mt-2 flex gap-4 font-mono text-[10px] text-slate-600">
                  <span>{new Date(r.created_at).toLocaleString()}</span>
                  {r.hypothesis_confidence !== null && <span>stated confidence: {(r.hypothesis_confidence * 100).toFixed(0)}%</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
