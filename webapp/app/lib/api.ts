// Client for the real WSQF-AI backend (wsqfai/server/main.py) - the same
// ingest -> measure -> hypothesize -> verify -> propose-fix pipeline the
// CLI runs, reachable over HTTP so a browser can drive it directly.
//
// Types here mirror the backend's actual pydantic models field-for-field
// (wsqfai/domain/evidence.py, wsqfai/remediation.py, wsqfai/report.py) -
// this is a thin client, not a reinterpretation of the report shape.

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export type Severity = "low" | "medium" | "high" | "critical";

export interface SourceLocation {
  file_path: string;
  start_line: number | null;
  end_line: number | null;
}

export interface AnalyzerMetadata {
  analyzer: string;
  rule_id: string | null;
  confidence: "low" | "medium" | "high";
}

export interface Evidence {
  evidence_id: string;
  location: SourceLocation;
  snippet: string;
  analyzer: AnalyzerMetadata;
  created_at: string;
}

export interface Observation {
  observation_id: string;
  description: string;
  location: SourceLocation | null;
  metadata: Record<string, string>;
}

export interface Finding {
  finding_id: string;
  title: string;
  description: string;
  characteristic: string;
  sub_characteristic_key: string;
  severity: Severity;
  evidence: Evidence[];
  related_observations: Observation[];
  created_at: string;
}

export interface Fix {
  finding_id: string;
  file_path: string;
  diff: string;
  summary: string;
  patched_content: string;
}

export interface Suggestion {
  finding_id: string;
  guidance: string;
}

export interface RepositoryReport {
  owner: string;
  repo: string;
  ref: string | null;
  total_files: number;
  total_lines: number;
  truncated: boolean;
  language_summary: Record<string, { files: number; lines: number }>;
  is_ml_repository: boolean;
  findings: Finding[];
  security_hypotheses: Observation[];
  fixes: Fix[];
  suggestions: Suggestion[];
}

export type JobStatus =
  | { status: "running" }
  | { status: "done"; result: RepositoryReport }
  | { status: "error"; error: string };

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function readErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // fall through to a generic message below
  }
  return `Request failed (${res.status})`;
}

// A thin wrapper so every call site gets the same, actually-informative
// message for the one failure mode `readErrorDetail` can't help with: the
// request never reached the server at all. `fetch` itself throws a bare
// TypeError for that (network down, wrong host, or - the likely real-world
// case once this is actually deployed - the backend's WSQFAI_ALLOWED_ORIGINS
// doesn't include this origin, so the browser blocks it as a CORS failure)
// with no detail a person could act on otherwise.
async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(
      `Couldn't reach the analysis backend at ${API_BASE_URL}. It may be down, or blocking ` +
        "requests from this site (a CORS setting on the backend) - see DEPLOYING.md if you're the one running it.",
      0,
    );
  }
}

export async function startAnalysis(repoUrl: string, ref?: string): Promise<string> {
  const res = await apiFetch("/api/analyze-repo/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl, ref: ref || null }),
  });
  if (!res.ok) throw new ApiError(await readErrorDetail(res), res.status);
  const data = (await res.json()) as { job_id: string };
  return data.job_id;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await apiFetch(`/api/analyze-repo/jobs/${jobId}`);
  if (!res.ok) throw new ApiError(await readErrorDetail(res), res.status);
  return (await res.json()) as JobStatus;
}

export function combinedPatch(report: RepositoryReport): string {
  return report.fixes.map((f) => f.diff).join("");
}

export interface OpenPrResult {
  pr_url: string;
  branch: string;
}

export async function openFixPr(
  repoUrl: string,
  fixes: Fix[],
  githubToken: string,
  baseBranch?: string,
): Promise<OpenPrResult> {
  const res = await apiFetch("/api/open-pr", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_url: repoUrl,
      fixes,
      github_token: githubToken,
      base_branch: baseBranch || null,
    }),
  });
  if (!res.ok) throw new ApiError(await readErrorDetail(res), res.status);
  return (await res.json()) as OpenPrResult;
}
