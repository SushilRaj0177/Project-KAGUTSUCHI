"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { useLanguage } from "@/components/LanguageContext";

interface CalibrationBucket {
  n: number;
  mean_stated_confidence: number;
}

interface CalibrationSummary {
  n: number;
  brier_score: number | null;
  buckets: Record<string, CalibrationBucket>;
  note?: string;
}

// Research-direction-D view (from the original brief): is the model's
// own stated confidence in an attack payload trustworthy? Backed by
// verification/calibration.py's method, computed here from real
// production `runs` rows rather than a Python library nobody sees.
export default function CalibrationPage() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [data, setData] = useState<CalibrationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/calibration")
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
        setData(body);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />

      <h2 className={`font-display mb-2 text-3xl font-extrabold ${jp}`}>{t.calibrationTitle}</h2>
      <p className={`mb-8 max-w-2xl text-sm leading-relaxed text-steel-400 ${jp}`}>{t.calibrationSubtitle}</p>

      {error && (
        <p className="border border-neon-pink/40 bg-neon-pink/10 p-3 font-mono text-xs text-neon-pink-soft">{error}</p>
      )}

      {data && data.n === 0 && (
        <div className="border border-dashed border-line-strong px-8 py-16 text-center">
          <h3 className={`font-display text-2xl font-extrabold ${jp}`}>{t.calibrationEmptyTitle}</h3>
          <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.calibrationEmptyBody}</p>
        </div>
      )}

      {data && data.n > 0 && (
        <div>
          <div className="mb-6 grid grid-cols-2 gap-px overflow-hidden border border-line bg-line">
            <div className="border-t-2 border-t-neon-cyan bg-void-900 p-5">
              <div className="text-[11px] text-steel-400 uppercase">{t.calibrationSampleSize}</div>
              <div className="font-display text-4xl font-extrabold">{data.n}</div>
            </div>
            <div className="border-t-2 border-t-neon-pink bg-void-900 p-5">
              <div className="text-[11px] text-steel-400 uppercase">{t.calibrationBrierScore}</div>
              <div className="font-display text-4xl font-extrabold">{data.brier_score?.toFixed(3)}</div>
            </div>
          </div>

          {data.note && (
            <p className={`mb-8 border border-line-strong bg-void-900 p-3 font-mono text-xs text-steel-400 ${jp}`}>
              {data.note}
            </p>
          )}

          <div className={`bracket-label mb-3 font-mono text-xs font-bold text-steel-400 uppercase ${jp}`}>
            {t.calibrationBuckets}
          </div>
          <div className="space-y-2">
            {Object.entries(data.buckets)
              .sort(([a], [b]) => parseInt(a) - parseInt(b))
              .map(([label, bucket]) => (
                <div key={label} className="flex items-center gap-3 border border-line bg-void-900/60 p-3 text-xs">
                  <span className="w-20 font-mono text-steel-400">{label}</span>
                  <div className="h-2 flex-1 bg-void-950">
                    <div
                      className="h-2 bg-neon-cyan"
                      style={{ width: `${Math.round(bucket.mean_stated_confidence * 100)}%` }}
                    />
                  </div>
                  <span className="w-16 text-right font-mono text-steel-400">n={bucket.n}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </main>
  );
}
