"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { useLanguage } from "@/components/LanguageContext";

interface CalibrationResponse {
  n: number;
  brier_score: number | null;
  buckets: Record<string, { n: number; mean_stated_confidence: number }>;
  note?: string;
  detail?: string;
}

export default function CalibrationPage() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
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

        <h1 className={`text-3xl font-bold sm:text-4xl ${jp}`}>{t.calibrationTitle}</h1>
        <p className={`mt-2 max-w-lg text-slate-400 ${jp}`}>{t.calibrationSubtitle}</p>

        {error && <p className="mt-6 rounded border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-300">{error}</p>}
        {data === null && !error && <p className={`mt-10 text-sm text-slate-500 ${jp}`}>{t.loading}</p>}

        {data && data.n === 0 && (
          <p className={`mt-10 rounded border border-dashed border-slate-800 p-8 text-center text-slate-400 ${jp}`}>
            {t.calibrationEmptyBody}{" "}
            <Link href="/scan" className="underline">
              {t.emptyBodyScanLink}
            </Link>
            .
          </p>
        )}

        {data && data.n > 0 && (
          <div className="mt-10 space-y-6">
            <div className="rounded border border-slate-800 bg-slate-900/40 p-6">
              <div className="text-4xl font-bold">{data.brier_score?.toFixed(3)}</div>
              <div className={`mt-1 text-xs text-slate-500 uppercase ${jp}`}>{t.calibrationBrierScore}</div>
              <div className={`mt-1 text-xs text-slate-600 ${jp}`}>{t.calibrationBrierSubtitle.replace("{n}", String(data.n))}</div>
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
                    <span className={`w-16 shrink-0 text-right font-mono text-xs text-slate-500 ${jp}`}>
                      {bucket.n} {t.calibrationSamplesShort}
                    </span>
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
