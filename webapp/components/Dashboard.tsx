"use client";

import { useState } from "react";
import type { RunRow } from "@/lib/db";
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
  label,
  jp,
  evidence,
  accent,
}: {
  label: string;
  jp: string;
  evidence: Record<string, unknown>;
  accent: "ember" | "temper";
}) {
  const border = accent === "ember" ? "border-t-ember-500" : "border-t-temper-500";
  const text = accent === "ember" ? "text-ember-300" : "text-temper-300";
  const created = Array.isArray((evidence as { filesystem_diff?: { created?: string[] } })?.filesystem_diff?.created)
    ? ((evidence as { filesystem_diff: { created: string[] } }).filesystem_diff.created)
    : [];
  const exitCode = evidence?.exit_code as number | undefined;
  const stderr = (evidence?.stderr as string | undefined) ?? "";

  return (
    <div className={`border border-line ${border} border-t-2 bg-void-900 p-4`}>
      <div className={`font-display text-sm font-extrabold uppercase tracking-wide ${text}`}>
        {label}
      </div>
      <div className="font-jp mb-3 text-[11px] text-steel-400">{jp}</div>
      <dl className="space-y-2 text-xs">
        <div className="flex justify-between gap-3">
          <dt className="text-steel-400">Exit code</dt>
          <dd className="font-mono tabular-nums">{exitCode ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-steel-400">Marker created</dt>
          <dd className="font-mono">
            {created.length > 0 ? created[created.length - 1] : "none"}
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
  const finding = run.finding as { symbol?: string; file_path?: string; rationale?: string };
  const hypothesis = run.hypothesis as { payload?: string; security_property?: string };

  return (
    <div className="space-y-4 border-t border-line bg-void-850 p-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <div className="font-jp text-[11px] text-steel-400">検知箇所 — Finding</div>
          <div className="font-mono text-sm text-paper-50">
            {finding?.file_path ?? "—"} · {finding?.symbol ?? "—"}
          </div>
          <p className="mt-1 text-xs text-steel-400">{finding?.rationale ?? ""}</p>
        </div>
        <div>
          <div className="font-jp text-[11px] text-steel-400">攻撃仮説 — Hypothesis</div>
          <p className="text-xs text-steel-400">{hypothesis?.security_property ?? ""}</p>
          {hypothesis?.payload && (
            <div className="mt-1 inline-block rounded-sm bg-void-950 px-2 py-1 font-mono text-xs text-gold-300">
              {hypothesis.payload}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <EvidenceColumn label="Before" jp="修正前" evidence={run.before_evidence} accent="ember" />
        <EvidenceColumn label="After" jp="修正後" evidence={run.after_evidence} accent="temper" />
      </div>

      <p className="border border-line-strong bg-void-900 p-3 text-sm text-paper-50">
        {run.summary}
      </p>
    </div>
  );
}

export function Dashboard({ runs }: { runs: RunRow[] }) {
  const [openId, setOpenId] = useState<string | null>(runs[0]?.id ?? null);

  const verifiedCount = runs.filter((r) => r.verdict === "VERIFIED_FIXED").length;
  const vulnerableCount = runs.filter((r) => r.verdict === "STILL_VULNERABLE").length;

  return (
    <div>
      <div className="mb-8 grid grid-cols-3 gap-px overflow-hidden border border-line bg-line">
        <StatTile label="Total Runs" jp="総検証数" value={runs.length} />
        <StatTile label="Verified Fixed" jp="修正確認" value={verifiedCount} tone="temper" />
        <StatTile label="Still Vulnerable" jp="未修正" value={vulnerableCount} tone="ember" />
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
  jp,
  value,
  tone,
}: {
  label: string;
  jp: string;
  value: number;
  tone?: "temper" | "ember";
}) {
  const valueColor =
    tone === "temper" ? "text-temper-300" : tone === "ember" ? "text-ember-300" : "text-paper-50";
  return (
    <div className="bg-void-900 p-5">
      <div className="font-jp text-[11px] text-steel-400">{jp}</div>
      <div className="text-[11px] uppercase tracking-wide text-steel-400">{label}</div>
      <div className={`font-display text-4xl font-extrabold tabular-nums ${valueColor}`}>
        {value}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="border border-dashed border-line-strong bg-void-900 px-8 py-16 text-center">
      <div className="font-jp text-2xl text-steel-400">空</div>
      <h2 className="font-display mt-2 text-2xl font-extrabold">No runs recorded yet</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-steel-400">
        This dashboard only shows real verification runs — nothing here is
        sample data. Run the pipeline and publish a result to see it appear:
      </p>
      <pre className="mx-auto mt-4 inline-block border border-line bg-void-950 px-4 py-3 text-left font-mono text-xs text-temper-300">
        PYTHONPATH=. python -m integration.publish_result demo
      </pre>
    </div>
  );
}
