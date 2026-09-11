export interface SecurityFinding {
  finding_id: string;
  file_path: string;
  symbol: string;
  diff_hunk: string;
  sensitive_op: string;
  rationale: string;
  detected_by: string;
  severity_hint: "low" | "medium" | "high";
}

export interface RepoResult {
  owner: string;
  repo: string;
  files_scanned: number;
  findings: SecurityFinding[];
  sources: Record<string, string>;
  truncated: boolean;
  commit_sha?: string;
}

export interface VerifyResult {
  hypothesis: { payload: string };
  before: { exit_code: number; filesystem_diff: { created?: string[] } };
  fixed_source: string | null;
  after: { filesystem_diff: { created?: string[] } } | null;
  result: { verdict: string; summary: string } | null;
  fix_error: string | null;
}

export const SEVERITY_COLOR: Record<string, string> = {
  high: "text-rose-400 border-rose-900",
  medium: "text-amber-400 border-amber-900",
  low: "text-slate-400 border-slate-700",
};
