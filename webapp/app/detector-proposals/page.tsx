"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface DetectorProposal {
  id: string;
  created_at: string;
  class_name: string;
  call_signature: string;
  rationale: string;
  severity_hint: string;
  source_file_path: string;
  source_repo: string | null;
  times_seen: number;
}

export default function DetectorProposalsPage() {
  const [proposals, setProposals] = useState<DetectorProposal[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/detector-proposals")
      .then((res) => res.json())
      .then((body) => {
        if (body.detail) setError(body.detail);
        else setProposals(body.proposals ?? []);
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

        <h1 className="text-3xl font-bold sm:text-4xl">New vulnerability classes</h1>
        <p className="mt-2 max-w-lg text-slate-400">
          The AI scanner reads code for meaning, not just fixed patterns. When it thinks it&apos;s found a
          vulnerability class outside the deterministic scanner&apos;s known list, it lands here — queued for human
          review, never auto-applied.
        </p>

        {error && <p className="mt-6 rounded border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-300">{error}</p>}
        {proposals === null && !error && <p className="mt-10 text-sm text-slate-500">Loading…</p>}

        {proposals && proposals.length === 0 && (
          <p className="mt-10 rounded border border-dashed border-slate-800 p-8 text-center text-slate-400">
            No proposals yet. Scan a repo whose vulnerabilities don&apos;t fit the known classes and the AI pass will
            surface one here.
          </p>
        )}

        {proposals && proposals.length > 0 && (
          <div className="mt-10 space-y-2">
            {proposals.map((p) => (
              <div key={p.id} className="rounded border border-slate-800 bg-slate-900/40 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-sm text-slate-200">{p.class_name}</span>
                  <span className="rounded border border-slate-700 px-2 py-0.5 font-mono text-[10px] text-slate-400 uppercase">
                    {p.severity_hint}
                  </span>
                </div>
                <div className="mt-1 font-mono text-xs text-slate-500">{p.call_signature}</div>
                <p className="mt-2 text-sm text-slate-400">{p.rationale}</p>
                <div className="mt-2 flex flex-wrap gap-4 font-mono text-[10px] text-slate-600">
                  <span>{p.source_file_path}</span>
                  {p.source_repo && <span>{p.source_repo}</span>}
                  <span>seen {p.times_seen}×</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
