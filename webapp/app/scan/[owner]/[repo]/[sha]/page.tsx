"use client";

import { use, useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { FindingCard, StatTile, downloadReport, type RepoAnalyzeResponse } from "@/components/RepoScanner";
import { useLanguage } from "@/components/LanguageContext";

// Shareable permalink for one specific (repo, commit) scan result -- a
// judge or teammate can be handed this URL directly instead of having to
// re-run the scan live. Read-only lookup into the cache analyze-repo
// already populates; if that exact commit was never scanned, this 404s
// rather than triggering a fresh scan on someone else's behalf.
export default function ScanPermalinkPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string; sha: string }>;
}) {
  const { owner, repo, sha } = use(params);
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [result, setResult] = useState<RepoAnalyzeResponse | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/scan-cache/${owner}/${repo}/${sha}`)
      .then(async (res) => {
        if (cancelled) return;
        if (res.status === 404) {
          setNotFound(true);
          return;
        }
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? `Request failed (${res.status})`);
        }
        setResult(await res.json());
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [owner, repo, sha]);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />

      <div className="mb-6 font-mono text-xs text-steel-400">
        {owner}/{repo} <span className="text-steel-600">@ {sha.slice(0, 12)}</span>
      </div>

      {notFound && (
        <div className="border border-dashed border-line-strong px-8 py-16 text-center">
          <h3 className={`font-display text-2xl font-extrabold ${jp}`}>{t.permalinkNotFoundTitle}</h3>
          <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.permalinkNotFoundBody}</p>
        </div>
      )}

      {error && (
        <p className="border border-neon-pink/40 bg-neon-pink/10 p-3 font-mono text-xs text-neon-pink-soft">{error}</p>
      )}

      {result && (
        <section className="border-t border-line pt-10">
          <div className="mb-8 grid grid-cols-2 gap-px overflow-hidden border border-line bg-line">
            <StatTile label={t.filesScanned} value={result.files_scanned} tone="cyan" />
            <StatTile label={t.findingsCount} value={result.findings.length} tone="pink" />
          </div>

          {result.truncated && (
            <p className={`mb-6 border border-line-strong bg-void-900 p-3 font-mono text-xs text-steel-400 ${jp}`}>
              {t.truncatedNotice}
            </p>
          )}

          <div className="mb-4 flex justify-end">
            <button
              type="button"
              data-cursor="hover"
              onClick={() => downloadReport(result)}
              className="border border-line-strong px-2 py-1 font-mono text-[10px] uppercase tracking-wide text-steel-400 transition-colors hover:border-neon-cyan hover:text-neon-cyan"
            >
              {t.downloadReport}
            </button>
          </div>

          {result.findings.length === 0 ? (
            <div className="border border-dashed border-line-strong px-8 py-16 text-center">
              <h3 className={`font-display text-2xl font-extrabold ${jp}`}>{t.noFindings}</h3>
              <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.noFindingsBody}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {result.findings.map((finding, i) => (
                <FindingCard
                  key={finding.finding_id}
                  finding={finding}
                  source={result.sources[finding.file_path]}
                  index={i}
                />
              ))}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
