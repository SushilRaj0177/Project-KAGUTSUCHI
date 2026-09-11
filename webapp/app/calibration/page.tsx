"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

interface CalibrationResponse {
  n: number;
  brier_score: number | null;
  buckets: Record<string, { n: number; mean_stated_confidence: number }>;
  note?: string;
  detail?: string;
}

export default function CalibrationPage() {
  const [data, setData] = useState<CalibrationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/calibration")
      .then((res) => res.json())
      .then((body) => {
        if (body.detail) setError(body.detail);
        else setData(body);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <SiteNav />

        <h1 className="text-3xl font-bold sm:text-4xl">Is the AI&apos;s confidence trustworthy?</h1>
        <p className="mt-2 max-w-lg text-slate-400">
          Every attack payload comes with the model&apos;s own stated confidence. This scores that confidence against
          what the sandbox actually observed, from real production runs.
        </p>

        {error && <p className="mt-6 rounded border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-300">{error}</p>}
        {data === null && !error && <p className="mt-10 text-sm text-slate-500">Loading…</p>}

        {data && data.n === 0 && (
          <p className="mt-10 rounded border border-dashed border-slate-800 p-8 text-center text-slate-400">
            No calibration data yet — run an attack on the <Link href="/scan" className="underline">scan page</Link> to
            generate some.
          </p>
        )}

        {data && data.n > 0 && (
          <div className="mt-10 space-y-6">
            <div className="rounded border border-slate-800 bg-slate-900/40 p-6">
              <div className="text-4xl font-bold">{data.brier_score?.toFixed(3)}</div>
              <div className="mt-1 text-xs text-slate-500 uppercase">Brier score — 0 is perfectly calibrated, 1 is worst</div>
              <div className="mt-1 text-xs text-slate-600">from {data.n} real attack{data.n === 1 ? "" : "s"}</div>
            </div>

            <div className="space-y-2">
              {Object.entries(data.buckets)
                .sort(([a], [b]) => parseInt(a) - parseInt(b))
                .map(([label, bucket]) => (
                  <div key={label} className="flex items-center gap-4 rounded border border-slate-800 p-3">
                    <span className="w-20 shrink-0 font-mono text-xs text-slate-400">{label}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded bg-slate-800">
                      <div className="h-full bg-white" style={{ width: `${bucket.mean_stated_confidence * 100}%` }} />
                    </div>
                    <span className="w-16 shrink-0 text-right font-mono text-xs text-slate-500">{bucket.n} sample{bucket.n === 1 ? "" : "s"}</span>
                  </div>
                ))}
            </div>

            {data.note && <p className="rounded border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-500">{data.note}</p>}
          </div>
        )}
      </div>
    </main>
  );
}
