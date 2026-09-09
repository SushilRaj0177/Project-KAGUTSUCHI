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
  accent,
}: {
  evidence: Record<string, unknown>;
  accent: "ember" | "temper";
}) {
  const { t, lang } = useLanguage();
  const label = accent === "ember" ? t.before : t.after;
  const border = accent === "ember" ? "border-t-ember-500" : "border-t-temper-500";
  const text = accent === "ember" ? "text-ember-300" : "text-temper-300";
  const jp = lang === "ja" ? "font-jp" : "";
  const created = Array.isArray((evidence as { filesystem_diff?: { created?: string[] } })?.filesystem_diff?.created)
    ? ((evidence as { filesystem_diff: { created: string[] } }).filesystem_diff.created)
    : [];
  const exitCode = evidence?.exit_code as number | undefined;
  const stderr = (evidence?.stderr as string | undefined) ?? "";

  return (
    <div className={`border border-line ${border} border-t-2 bg-void-900 p-4`}>
      <div className={`text-sm font-bold ${text} ${jp}`}>{label}</div>
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
        <pre className="mt-3 max-h-28 overflow-y-auto whitespace-pre-wrap break-words border border-line bg-void-950 p-2 font-mono text-[11px] text-steel-400">
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

  return (
    <div className="space-y-4 border-t border-line bg-void-850 p-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <div className={`text-sm font-bold text-paper-50 ${jp}`}>{t.finding}</div>
          <div className="font-mono text-sm text-paper-50">
            {finding?.file_path ?? "—"} · {finding?.symbol ?? "—"}
          </div>
          <p className="mt-1 text-xs text-steel-400">{finding?.rationale ?? ""}</p>
        </div>
        <div>
          <div className={`text-sm font-bold text-paper-50 ${jp}`}>{t.hypothesis}</div>
          <p className="text-xs text-steel-400">{hypothesis?.security_property ?? ""}</p>
          {hypothesis?.payload && (
            <div className="mt-1 inline-block rounded-sm bg-void-950 px-2 py-1 font-mono text-xs text-gold-300">
              {hypothesis.payload}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <EvidenceColumn evidence={run.before_evidence} accent="ember" />
        <EvidenceColumn evidence={run.after_evidence} accent="temper" />
      </div>

      <p className="border border-line-strong bg-void-900 p-3 text-sm text-paper-50">
        {run.summary}
      </p>
    </div>
  );
}

export function Dashboard({ runs }: { runs: RunRow[] }) {
  const { t } = useLanguage();
  const [openId, setOpenId] = useState<string | null>(runs[0]?.id ?? null);

  const verifiedCount = runs.filter((r) => r.verdict === "VERIFIED_FIXED").length;
  const vulnerableCount = runs.filter((r) => r.verdict === "STILL_VULNERABLE").length;

  return (
    <div>
      <div className="mb-8 grid grid-cols-3 gap-px overflow-hidden border border-line bg-line">
        <StatTile label={t.statTotal} value={runs.length} />
        <StatTile label={t.statVerified} value={verifiedCount} tone="temper" />
        <StatTile label={t.statVulnerable} value={vulnerableCount} tone="ember" />
      </div>

      {runs.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="border border-line">
          {runs.map((run) => {
            const isOpen = openId === run.id;
            return (
              <div key={run.id} className="border-b border-line last:border-b-0">
                <button
                  onClick={() => setOpenId(isOpen ? null : run.id)}
                  className="flex w-full items-center justify-between gap-4 bg-void-900 px-5 py-4 text-left hover:bg-void-850"
                >
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-xs text-steel-400 tabular-nums">
                      {formatTimestamp(run.created_at)}
                    </span>
                    <span className="font-display text-base font-bold">
                      {run.fixture_name}
                    </span>
                    <span className="rounded-sm border border-line-strong px-2 py-0.5 text-[11px] uppercase text-steel-400">
                      {run.sensitive_op}
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
  tone?: "temper" | "ember";
}) {
  const { lang } = useLanguage();
  const valueColor =
    tone === "temper" ? "text-temper-300" : tone === "ember" ? "text-ember-300" : "text-paper-50";
  return (
    <div className="bg-void-900 p-5">
      <div className={`text-[11px] uppercase tracking-wide text-steel-400 ${lang === "ja" ? "font-jp normal-case" : ""}`}>
        {label}
      </div>
      <div className={`font-display text-4xl font-extrabold tabular-nums ${valueColor}`}>
        {value}
      </div>
    </div>
  );
}

function EmptyState() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  return (
    <div className="border border-dashed border-line-strong bg-void-900 px-8 py-16 text-center">
      <div className="font-jp text-2xl text-steel-400">空</div>
      <h2 className={`font-display mt-2 text-2xl font-extrabold ${jp}`}>{t.emptyTitle}</h2>
      <p className={`mx-auto mt-2 max-w-md text-sm text-steel-400 ${jp}`}>{t.emptyBody}</p>
      <pre className="mx-auto mt-4 inline-block border border-line bg-void-950 px-4 py-3 text-left font-mono text-xs text-temper-300">
        PYTHONPATH=. python -m integration.publish_result demo
      </pre>
    </div>
  );
}
