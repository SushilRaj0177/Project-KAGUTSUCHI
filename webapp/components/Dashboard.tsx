"use client";

import { useState } from "react";
import type { RunRow } from "@/lib/db";
import { useLanguage } from "./LanguageContext";
import { VerdictBadge } from "./VerdictBadge";

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function EvidenceColumn({
  evidence,
  label,
  tone,
}: {
  evidence: Record<string, unknown>;
  label: string;
  tone: "pink" | "cyan";
}) {
  const { t } = useLanguage();
  const created = Array.isArray((evidence as { filesystem_diff?: { created?: string[] } })?.filesystem_diff?.created)
    ? ((evidence as { filesystem_diff: { created: string[] } }).filesystem_diff.created)
    : [];
  const exitCode = evidence?.exit_code as number | undefined;
  const stderr = (evidence?.stderr as string | undefined) ?? "";
  const border = tone === "pink" ? "border-t-neon-pink" : "border-t-neon-cyan";
  const text = tone === "pink" ? "neon-text-pink" : "neon-text-cyan";

  return (
    <div className={`border border-line border-t-2 ${border} p-4`}>
      <div className={`text-sm font-bold ${text}`}>{label}</div>
      <dl className="mt-3 space-y-2 text-xs">
        <div className="flex justify-between gap-3">
          <dt className="text-steel-400">{t.exitCode}</dt>
          <dd className="font-mono tabular-nums">{exitCode ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-steel-400">{t.markerCreated}</dt>
          <dd className="font-mono">
            {created.length > 0 ? created[created.length - 1] : t.none}
          </dd>
        </div>
      </dl>
      {stderr && (
        <pre className="mt-3 max-h-28 overflow-y-auto whitespace-pre-wrap break-words border border-line p-2 font-mono text-[11px] text-steel-400">
          {stderr}
        </pre>
      )}
    </div>
  );
}

function RunDetail({ run }: { run: RunRow }) {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const finding = run.finding as { symbol?: string; file_path?: string; rationale?: string };
  const hypothesis = run.hypothesis as { payload?: string; security_property?: string };

  const plainSummary =
    run.verdict === "VERIFIED_FIXED"
      ? t.plainVerifiedFixed
      : run.verdict === "STILL_VULNERABLE"
        ? t.plainStillVulnerable
        : t.plainOther;

  return (
    <div className="space-y-6 border-t border-line p-5">
      <div>
        <div className={`text-xs font-bold tracking-wide neon-text-cyan uppercase ${jp}`}>{t.whatHappened}</div>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-paper-50">{plainSummary}</p>
      </div>

      <div>
        <div className={`bracket-label mb-3 font-mono text-xs font-bold text-steel-400 uppercase ${jp}`}>
          {t.technicalDetails}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className={`font-mono text-sm font-bold text-paper-50 ${jp}`}>{t.finding}</div>
            <div className="font-mono text-sm text-paper-50">
              {finding?.file_path ?? "—"} · {finding?.symbol ?? "—"}
            </div>
            <p className="mt-1 text-xs text-steel-400">{finding?.rationale ?? ""}</p>
          </div>
          <div>
            <div className={`font-mono text-sm font-bold text-paper-50 ${jp}`}>{t.hypothesis}</div>
            <p className="text-xs text-steel-400">{hypothesis?.security_property ?? ""}</p>
            {hypothesis?.payload && (
              <div className="mt-1 inline-block border border-line px-2 py-1 font-mono text-xs text-paper-50">
                {hypothesis.payload}
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <EvidenceColumn evidence={run.before_evidence} label={t.before} tone="pink" />
          <EvidenceColumn evidence={run.after_evidence} label={t.after} tone="cyan" />
        </div>

        <p className="mt-4 border border-line-strong p-3 text-sm text-paper-50">{run.summary}</p>
      </div>
    </div>
  );
}

export function Dashboard({ runs }: { runs: RunRow[] }) {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [openId, setOpenId] = useState<string | null>(runs[0]?.id ?? null);

  const verifiedCount = runs.filter((r) => r.verdict === "VERIFIED_FIXED").length;
  const vulnerableCount = runs.filter((r) => r.verdict === "STILL_VULNERABLE").length;

  return (
    <div>
      <div className="mb-8 grid grid-cols-3 gap-px overflow-hidden border border-line bg-line">
        <StatTile label={t.statTotal} value={runs.length} tone="neutral" />
        <StatTile label={t.statVerified} value={verifiedCount} tone="cyan" />
        <StatTile label={t.statVulnerable} value={vulnerableCount} tone="pink" />
      </div>

      {runs.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="border border-line">
          {runs.map((run) => {
            const isOpen = openId === run.id;
            const vulnLabel = t.vulnClass[run.sensitive_op] ?? run.sensitive_op;
            return (
              <div key={run.id} className="border-b border-line last:border-b-0">
                <button
                  onClick={() => setOpenId(isOpen ? null : run.id)}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left hover:bg-void-900"
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <span className={`font-display text-base font-bold ${jp}`}>{vulnLabel}</span>
                    <span className="font-mono text-xs text-steel-400 tabular-nums">
                      {formatTimestamp(run.created_at)}
                    </span>
                    <span className="border border-line-strong px-2 py-0.5 font-mono text-[11px] text-steel-400">
                      {run.fixture_name}
                    </span>
                  </div>
                  <VerdictBadge verdict={run.verdict} />
                </button>
                {isOpen && <RunDetail run={run} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "cyan" | "pink" | "neutral";
}) {
  const { lang } = useLanguage();
  const border = tone === "cyan" ? "border-t-neon-cyan" : tone === "pink" ? "border-t-neon-pink" : "border-t-paper-50";
  return (
    <div className={`border-t-2 bg-void-900 p-5 ${border}`}>
      <div className={`text-[11px] uppercase tracking-wide text-steel-400 ${lang === "ja" ? "font-jp normal-case" : ""}`}>
        {label}
      </div>
      <div className="font-display text-4xl font-extrabold tabular-nums text-paper-50">{value}</div>
    </div>
  );
}

function EmptyState() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  return (
    <div className="border border-dashed border-line-strong px-8 py-16 text-center">
      <div className="font-jp text-2xl text-steel-400">空</div>
      <h2 className={`font-display mt-2 text-2xl font-extrabold ${jp}`}>{t.emptyTitle}</h2>
      <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.emptyBody}</p>
      <pre className="mx-auto mt-4 inline-block border border-line px-4 py-3 text-left font-mono text-xs text-paper-50">
        PYTHONPATH=. python -m integration.publish_result demo
      </pre>
    </div>
  );
}
