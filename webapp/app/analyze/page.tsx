"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import {
  ApiError,
  combinedPatch,
  getJobStatus,
  openFixPr,
  startAnalysis,
  type Fix,
  type OpenPrResult,
  type RepositoryReport,
  type Severity,
} from "../lib/api";
import { spawnRipple } from "../components/ripple";

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];
const POLL_INTERVAL_MS = 2000;

type RunState =
  | { phase: "idle" }
  | { phase: "running" }
  | { phase: "done"; report: RepositoryReport }
  | { phase: "error"; message: string };

export default function AnalyzePage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [ref, setRef] = useState("");
  const [state, setState] = useState<RunState>({ phase: "idle" });
  const [elapsedS, setElapsedS] = useState(0);
  const pollHandle = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (pollHandle.current) clearTimeout(pollHandle.current);
    };
  }, []);

  useEffect(() => {
    if (state.phase !== "running") return;
    const interval = setInterval(() => setElapsedS((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [state.phase]);

  async function poll(jobId: string) {
    try {
      const status = await getJobStatus(jobId);
      if (status.status === "running") {
        pollHandle.current = setTimeout(() => poll(jobId), POLL_INTERVAL_MS);
        return;
      }
      if (status.status === "error") {
        setState({ phase: "error", message: status.error });
        return;
      }
      setState({ phase: "done", report: status.result });
    } catch (err) {
      setState({ phase: "error", message: describeError(err) });
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setElapsedS(0);
    setState({ phase: "running" });
    try {
      const jobId = await startAnalysis(repoUrl.trim(), ref.trim() || undefined);
      poll(jobId);
    } catch (err) {
      setState({ phase: "error", message: describeError(err) });
    }
  }

  function handleDownloadPatch(report: RepositoryReport) {
    const patch = combinedPatch(report);
    const blob = new Blob([patch], { type: "text/x-diff" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.owner}-${report.repo}.patch`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main>
      <section className="hero" style={{ paddingBottom: 24 }}>
        <div className="wrap">
          <span className="eyebrow">Run it in the browser</span>
          <h1>Analyze a public repository</h1>
          <p className="lede">
            Paste a GitHub URL. This calls the same ingest → measure → hypothesize → verify pipeline the CLI
            runs — nothing to install.
          </p>

          <form className="analyze-form" onSubmit={handleSubmit}>
            <input
              type="text"
              inputMode="url"
              placeholder="https://github.com/owner/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={state.phase === "running"}
              required
            />
            <input
              type="text"
              placeholder="branch or tag (optional)"
              value={ref}
              onChange={(e) => setRef(e.target.value)}
              disabled={state.phase === "running"}
              className="analyze-ref"
            />
            <motion.button
              type="submit"
              className="ripple-host"
              onPointerDown={spawnRipple}
              whileTap={{ scale: 0.97 }}
              disabled={state.phase === "running"}
            >
              {state.phase === "running" ? "Analyzing…" : "Run analysis"}
            </motion.button>
          </form>

          {state.phase === "running" && (
            <p className="analyze-status">
              <span className="analyze-spinner" aria-hidden /> {runningMessage(elapsedS)}
            </p>
          )}
          {state.phase === "error" && <p className="analyze-status analyze-status-error">{state.message}</p>}
        </div>
      </section>

      {state.phase === "done" && <ReportView report={state.report} onDownloadPatch={handleDownloadPatch} />}
    </main>
  );
}

function describeError(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Something went wrong reaching the analysis backend.";
}

// A real scan can take anywhere from a few seconds (a tiny repo) to a
// couple of minutes (a large one, or a cold backend on a free-tier host
// waking up) - a static "this can take a minute" message reads as broken
// once the actual wait runs past what it promised. Escalating the wording
// with elapsed time keeps it honest instead.
function runningMessage(elapsedS: number): string {
  if (elapsedS < 20) return "Cloning and analyzing — this can take a minute for a larger repository.";
  if (elapsedS < 60) return `Still going (${elapsedS}s) — cloning and running the full measurement/security pipeline.`;
  return `Still going (${elapsedS}s) — a cold backend or a large repository can take a few minutes. No need to retry.`;
}

function ReportView({
  report,
  onDownloadPatch,
}: {
  report: RepositoryReport;
  onDownloadPatch: (report: RepositoryReport) => void;
}) {
  const bySeverity: Partial<Record<Severity, number>> = {};
  for (const f of report.findings) bySeverity[f.severity] = (bySeverity[f.severity] ?? 0) + 1;

  const sortedFindings = [...report.findings].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity),
  );

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <div className="wrap">
        <h2>
          {report.owner}/{report.repo}
          {report.ref ? `@${report.ref}` : ""}
        </h2>

        <div className="stats">
          <div className="stat">
            <span className="n">{report.total_files}</span>
            <span className="l">files scanned</span>
          </div>
          <div className="stat">
            <span className="n">{report.total_lines}</span>
            <span className="l">lines</span>
          </div>
          <div className="stat">
            <span className="n">{report.findings.length}</span>
            <span className="l">findings</span>
          </div>
          <div className="stat">
            <span className="n">{report.security_hypotheses.length}</span>
            <span className="l">security hypotheses</span>
          </div>
          <div className="stat">
            <span className="n">{report.fixes.length}</span>
            <span className="l">fixes proposed</span>
          </div>
          <div className="stat">
            <span className="n">{report.is_ml_repository ? "yes" : "no"}</span>
            <span className="l">ML-containing</span>
          </div>
        </div>

        <h3 style={{ marginTop: 40 }}>Findings</h3>
        {sortedFindings.length === 0 ? (
          <p className="lede" style={{ fontSize: "0.95rem" }}>
            No findings.
          </p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Sub-characteristic</th>
                  <th>Finding</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                {sortedFindings.map((f) => (
                  <tr key={f.finding_id}>
                    <td>
                      <span className={`sev ${f.severity}`}>{f.severity.toUpperCase()}</span>
                    </td>
                    <td className="loc">
                      {f.characteristic}/{f.sub_characteristic_key}
                    </td>
                    <td>{f.title}</td>
                    <td className="loc">{f.evidence[0]?.location.file_path ?? "?"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {report.security_hypotheses.length > 0 && (
          <>
            <h3 style={{ marginTop: 40 }}>Security hypotheses</h3>
            <p className="lede" style={{ fontSize: "0.9rem" }}>
              Raw static matches — a sandbox-confirmed one is also promoted to a Finding above.
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Op</th>
                    <th>Rationale</th>
                    <th>Location</th>
                  </tr>
                </thead>
                <tbody>
                  {report.security_hypotheses.map((o) => (
                    <tr key={o.observation_id}>
                      <td>
                        <span className={`sev ${o.metadata.severity_hint ?? "medium"}`}>
                          {(o.metadata.severity_hint ?? "?").toUpperCase()}
                        </span>
                      </td>
                      <td className="loc">{o.metadata.sensitive_op ?? "?"}</td>
                      <td>{o.description}</td>
                      <td className="loc">
                        {o.location ? `${o.location.file_path}:${o.location.start_line ?? "?"}` : "?"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {(report.fixes.length > 0 || report.suggestions.length > 0) && (
          <>
            <div className="fixes-header">
              <h3 style={{ marginTop: 40 }}>Proposed fixes</h3>
              {report.fixes.length > 0 && (
                <button className="ripple-host" onPointerDown={spawnRipple} onClick={() => onDownloadPatch(report)}>
                  Download patch
                </button>
              )}
            </div>
            {report.fixes.map((fix) => (
              <div key={fix.finding_id}>
                <p className="fix-summary">
                  <code>{fix.file_path}</code> — {fix.summary}
                </p>
                <pre className="pipeline-pre">{fix.diff}</pre>
              </div>
            ))}
            {report.suggestions.map((s) => (
              <p key={s.finding_id} className="fix-summary">
                Suggestion (not auto-applied): {s.guidance}
              </p>
            ))}
          </>
        )}

        {report.fixes.length > 0 && <OpenPrPanel repoUrl={`https://github.com/${report.owner}/${report.repo}`} fixes={report.fixes} />}
      </div>
    </motion.section>
  );
}

type OpenPrState =
  | { phase: "idle" }
  | { phase: "submitting" }
  | { phase: "done"; result: OpenPrResult }
  | { phase: "error"; message: string };

function OpenPrPanel({ repoUrl, fixes }: { repoUrl: string; fixes: Fix[] }) {
  const [token, setToken] = useState("");
  const [baseBranch, setBaseBranch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(() => new Set(fixes.map((f) => f.finding_id)));
  const [state, setState] = useState<OpenPrState>({ phase: "idle" });

  function toggle(findingId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(findingId)) next.delete(findingId);
      else next.add(findingId);
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const chosen = fixes.filter((f) => selected.has(f.finding_id));
    if (!token.trim() || chosen.length === 0) return;
    setState({ phase: "submitting" });
    try {
      const result = await openFixPr(repoUrl, chosen, token.trim(), baseBranch.trim() || undefined);
      setState({ phase: "done", result });
    } catch (err) {
      setState({ phase: "error", message: describeError(err) });
    }
  }

  if (state.phase === "done") {
    return (
      <div className="open-pr-panel">
        <h3>Pull request opened</h3>
        <p className="lede" style={{ fontSize: "0.95rem" }}>
          <a className="inline-link" href={state.result.pr_url} target="_blank" rel="noreferrer">
            {state.result.pr_url} <span className="arrow">→</span>
          </a>{" "}
          on branch <code>{state.result.branch}</code>.
        </p>
      </div>
    );
  }

  return (
    <div className="open-pr-panel">
      <h3>Open a pull request with these fixes</h3>
      <p className="lede" style={{ fontSize: "0.9rem" }}>
        Needs a GitHub token with write access to this repo — sent directly to the backend for this one request,
        never stored or logged (see `wsqfai/integration/github_pr.py`).
      </p>
      <form className="open-pr-form" onSubmit={handleSubmit}>
        <div className="open-pr-fixes">
          {fixes.map((fix) => (
            <label key={fix.finding_id} className="open-pr-fix-row">
              <input type="checkbox" checked={selected.has(fix.finding_id)} onChange={() => toggle(fix.finding_id)} />
              <code>{fix.file_path}</code> — {fix.summary}
            </label>
          ))}
        </div>
        <div className="analyze-form">
          <input
            type="password"
            placeholder="GitHub token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            disabled={state.phase === "submitting"}
            required
          />
          <input
            type="text"
            placeholder="base branch (optional)"
            value={baseBranch}
            onChange={(e) => setBaseBranch(e.target.value)}
            disabled={state.phase === "submitting"}
            className="analyze-ref"
          />
          <motion.button
            type="submit"
            className="ripple-host"
            onPointerDown={spawnRipple}
            whileTap={{ scale: 0.97 }}
            disabled={state.phase === "submitting" || selected.size === 0}
          >
            {state.phase === "submitting" ? "Opening…" : "Open PR"}
          </motion.button>
        </div>
        {state.phase === "error" && <p className="analyze-status analyze-status-error">{state.message}</p>}
      </form>
    </div>
  );
}
