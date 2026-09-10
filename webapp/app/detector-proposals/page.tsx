"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { useLanguage } from "@/components/LanguageContext";

interface Proposal {
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

// Where the AI scanner's "here's a vulnerability class your fixed
// pattern list doesn't know about yet" signal actually surfaces. Every
// row here is a candidate NEW entry for ast_scan.py's deterministic
// _SIGNATURES table -- never auto-applied (see system/analysis/
// llm_scan.py's docstring for why), promoted manually via
// scripts/promote_detector.py once a human/session reviews it. This is
// the mechanism for "the deterministic list keeps expanding, and nothing
// genuinely novel gets silently missed in the meantime."
export default function DetectorProposalsPage() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [proposals, setProposals] = useState<Proposal[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/detector-proposals")
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
        setProposals(body.proposals);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />

      <h2 className={`font-display mb-2 text-3xl font-extrabold ${jp}`}>{t.detectorProposalsTitle}</h2>
      <p className={`mb-8 max-w-2xl text-sm leading-relaxed text-steel-400 ${jp}`}>
        {t.detectorProposalsSubtitle}
      </p>

      {error && (
        <p className="border border-neon-pink/40 bg-neon-pink/10 p-3 font-mono text-xs text-neon-pink-soft">{error}</p>
      )}

      {proposals && proposals.length === 0 && (
        <div className="border border-dashed border-line-strong px-8 py-16 text-center">
          <h3 className={`font-display text-2xl font-extrabold ${jp}`}>{t.detectorProposalsEmptyTitle}</h3>
          <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.detectorProposalsEmptyBody}</p>
        </div>
      )}

      {proposals && proposals.length > 0 && (
        <div className="space-y-3">
          {proposals.map((p) => (
            <div key={p.id} className="border border-line bg-void-900/60 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-display text-lg font-bold">{p.class_name}</span>
                <div className="flex items-center gap-2">
                  {p.times_seen > 1 && (
                    <span className="border border-neon-cyan/40 px-2 py-0.5 font-mono text-[10px] text-neon-cyan uppercase">
                      {t.detectorProposalsSeenTimes.replace("{n}", String(p.times_seen))}
                    </span>
                  )}
                  <span
                    className={`border px-2 py-0.5 font-mono text-[10px] uppercase ${
                      p.severity_hint === "high" ? "border-neon-pink/40 text-neon-pink-soft" : "border-line-strong text-steel-400"
                    }`}
                  >
                    {p.severity_hint}
                  </span>
                </div>
              </div>
              <div className="mt-2 inline-block border border-line bg-void-950 px-2 py-1 font-mono text-xs text-paper-50">
                {p.call_signature}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-paper-50">{p.rationale}</p>
              <p className="mt-2 font-mono text-[11px] text-steel-400">
                {t.detectorProposalsSpottedIn}: {p.source_repo ?? p.source_file_path}
              </p>
              <pre className="mt-3 border border-line-strong bg-void-950 p-2 font-mono text-[11px] text-steel-400">
                python scripts/promote_detector.py {p.id}
              </pre>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
