"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { MagneticButton } from "@/components/MagneticButton";
import { useLanguage } from "@/components/LanguageContext";

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
}

// Answers "did this branch/PR introduce a new vulnerability class" (or
// fix one) directly, instead of running two separate scans and eyeballing
// the difference. Real value for a "gate merges on new vulnerabilities"
// workflow, even in this manual form.
export default function ComparePage() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [repoUrl, setRepoUrl] = useState("");
  const [baseRef, setBaseRef] = useState("");
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
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          base_ref: baseRef.trim(),
          head_ref: headRef.trim(),
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />

      <h2 className={`font-display mb-2 text-3xl font-extrabold ${jp}`}>{t.compareTitle}</h2>
      <p className={`mb-8 max-w-xl text-sm text-steel-400 ${jp}`}>{t.compareSubtitle}</p>

      <form onSubmit={handleSubmit} className="hud-frame mb-10 max-w-xl space-y-3 border border-line-strong bg-void-900/70 p-4">
        <input
          data-cursor="hover"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder={t.repoPlaceholder}
          className="w-full border border-line-strong bg-void-950 px-3 py-2 font-mono text-sm text-paper-50 outline-none placeholder:text-steel-600 focus:border-neon-cyan"
        />
        <div className="flex gap-3">
          <input
            data-cursor="hover"
            value={baseRef}
            onChange={(e) => setBaseRef(e.target.value)}
            placeholder={t.baseRefPlaceholder}
            className="flex-1 border border-line-strong bg-void-950 px-3 py-2 font-mono text-sm text-paper-50 outline-none placeholder:text-steel-600 focus:border-neon-cyan"
          />
          <input
            data-cursor="hover"
            value={headRef}
            onChange={(e) => setHeadRef(e.target.value)}
            placeholder={t.headRefPlaceholder}
            className="flex-1 border border-line-strong bg-void-950 px-3 py-2 font-mono text-sm text-paper-50 outline-none placeholder:text-steel-600 focus:border-neon-cyan"
          />
        </div>
        <MagneticButton
          type="submit"
          disabled={loading}
          className={`neon-border-pink w-full border border-neon-pink bg-neon-pink/10 px-6 py-2.5 text-xs font-bold tracking-[0.2em] text-neon-pink-soft uppercase transition-colors hover:bg-neon-pink/25 disabled:cursor-wait disabled:opacity-50 ${jp}`}
        >
          {loading ? t.comparingButton : t.compareButton}
        </MagneticButton>
      </form>

      {error && (
        <p className="mb-6 max-w-xl border border-neon-pink/40 bg-neon-pink/10 p-3 font-mono text-xs text-neon-pink-soft">
          {error}
        </p>
      )}

      {result && (
        <div className="space-y-8">
          <div className="grid grid-cols-3 gap-px overflow-hidden border border-line bg-line">
            <div className="border-t-2 border-t-neon-pink bg-void-900 p-4">
              <div className="text-[11px] text-steel-400 uppercase">{t.compareAdded}</div>
              <div className="font-display text-3xl font-extrabold">{result.added.length}</div>
            </div>
            <div className="border-t-2 border-t-neon-cyan bg-void-900 p-4">
              <div className="text-[11px] text-steel-400 uppercase">{t.compareRemoved}</div>
              <div className="font-display text-3xl font-extrabold">{result.removed.length}</div>
            </div>
            <div className="border-t-2 border-t-line-strong bg-void-900 p-4">
              <div className="text-[11px] text-steel-400 uppercase">{t.compareUnchanged}</div>
              <div className="font-display text-3xl font-extrabold">{result.unchanged_count}</div>
            </div>
          </div>

          {result.added.length > 0 && (
            <div>
              <div className={`mb-2 text-xs font-bold uppercase neon-text-pink ${jp}`}>{t.compareAddedTitle}</div>
              <div className="space-y-2">
                {result.added.map((f) => (
                  <div key={f.finding_id} className="border border-neon-pink/30 bg-void-900/60 p-3 text-xs">
                    <div className="font-bold">{t.vulnClass[f.sensitive_op] ?? f.sensitive_op}</div>
                    <div className="font-mono text-steel-400">
                      {f.file_path} — {f.symbol}()
                    </div>
                    <p className="mt-1 text-steel-400">{f.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.removed.length > 0 && (
            <div>
              <div className={`mb-2 text-xs font-bold uppercase neon-text-cyan ${jp}`}>{t.compareRemovedTitle}</div>
              <div className="space-y-2">
                {result.removed.map((f) => (
                  <div key={f.finding_id} className="border border-neon-cyan/30 bg-void-900/60 p-3 text-xs">
                    <div className="font-bold">{t.vulnClass[f.sensitive_op] ?? f.sensitive_op}</div>
                    <div className="font-mono text-steel-400">
                      {f.file_path} — {f.symbol}()
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.added.length === 0 && result.removed.length === 0 && (
            <p className={`text-sm text-steel-400 ${jp}`}>{t.compareNoDiff}</p>
          )}
        </div>
      )}
    </main>
  );
}
