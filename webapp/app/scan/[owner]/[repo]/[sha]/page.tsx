"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { FindingCard } from "@/components/FindingCard";
import { useLanguage } from "@/components/LanguageContext";
import type { RepoResult } from "@/lib/scanTypes";

export default function ScanPermalinkPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string; sha: string }>;
}) {
  const { owner, repo, sha } = use(params);
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [result, setResult] = useState<RepoResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/scan-cache/${owner}/${repo}/${sha}`)
      .then((res) => res.json())
      .then((body) => {
        if (body.detail) setError(body.detail);
        else setResult(body);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [owner, repo, sha]);

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <SiteNav />

        <h1 className="text-3xl font-bold sm:text-4xl">
          {owner}/{repo}
        </h1>
        <p className="mt-2 font-mono text-xs text-slate-500">@ {sha}</p>

        {error && (
          <div className={`mt-6 rounded border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400 ${jp}`}>
            <p>{error}</p>
            <p className="mt-3">
              {t.permalinkNotFoundBody}{" "}
              <Link href="/scan" className="underline">
                {t.permalinkRunFreshScan}
              </Link>
            </p>
          </div>
        )}

        {!result && !error && <p className={`mt-10 text-sm text-slate-500 ${jp}`}>{t.loading}</p>}

        {result && (
          <div className="mt-12">
            <div className="mb-6 grid grid-cols-2 gap-px overflow-hidden rounded border border-slate-800 bg-slate-800">
              <div className="bg-slate-950 p-4">
                <div className="text-3xl font-bold">{result.files_scanned}</div>
                <div className={`text-xs text-slate-500 uppercase ${jp}`}>{t.filesScanned}</div>
              </div>
              <div className="bg-slate-950 p-4">
                <div className="text-3xl font-bold">{result.findings.length}</div>
                <div className={`text-xs text-slate-500 uppercase ${jp}`}>{t.findingsCount}</div>
              </div>
            </div>

            {result.findings.length === 0 ? (
              <p className={`rounded border border-dashed border-slate-800 p-8 text-center text-slate-400 ${jp}`}>
                {t.noFindingsBody}
              </p>
            ) : (
              <div className="space-y-2">
                {result.findings.map((f) => (
                  <FindingCard
                    key={f.finding_id}
                    finding={f}
                    source={result.sources[f.file_path]}
                    repoOwner={result.owner ?? owner}
                    repoName={result.repo ?? repo}
                  />
                ))}
              </div>
            )}

            <p className={`mt-6 text-xs text-slate-600 ${jp}`}>
              {t.permalinkFooterNote}{" "}
              <Link href="/scan" className="underline">
                {t.permalinkFooterScanLink}
              </Link>
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
