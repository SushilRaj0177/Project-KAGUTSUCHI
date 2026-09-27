import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";
import { listApprovedLearnedSignatures } from "@/lib/db";

// Runs two full repo scans (one per ref) and diffs the findings -- lets
// someone answer "did this PR/branch introduce a new vulnerability
// class" directly, instead of eyeballing two separate scan results.
// Deliberately calls the backend directly rather than going through the
// cached /api/backend/analyze-repo route: that cache is keyed off the
// default branch's HEAD sha, and a base/head comparison is almost always
// two non-default refs anyway, so there's little cache benefit to chase
// here for the added complexity.
export const maxDuration = 60;

interface Finding {
  finding_id: string;
  file_path: string;
  symbol: string;
  sensitive_op: string;
  severity_hint: string;
  rationale: string;
  diff_hunk: string;
}

interface ScanResult {
  files_scanned: number;
  findings: Finding[];
  truncated: boolean;
}

function findingKey(f: Finding): string {
  return `${f.file_path}::${f.symbol}::${f.sensitive_op}`;
}

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  let body: { repo_url?: string; base_ref?: string; head_ref?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Malformed request body" }, { status: 400 });
  }
  const { repo_url, base_ref, head_ref } = body;
  if (!repo_url || !base_ref || !head_ref) {
    return NextResponse.json({ detail: "repo_url, base_ref, and head_ref are all required" }, { status: 400 });
  }

  const ip = clientIp(request);
  const learnedSignatures = await listApprovedLearnedSignatures().catch(() => []);
  const scanRef = async (ref: string): Promise<ScanResult> => {
    const res = await fetch(`${backendUrl.replace(/\/$/, "")}/api/analyze-repo`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Client-IP": ip },
      body: JSON.stringify({ repo_url, ref, learned_signatures: learnedSignatures }),
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail ?? `Scanning ${ref} failed (${res.status})`);
    }
    return res.json();
  };

  try {
    const [base, head] = await Promise.all([scanRef(base_ref), scanRef(head_ref)]);

    const baseKeys = new Set(base.findings.map(findingKey));
    const headKeys = new Set(head.findings.map(findingKey));

    const added = head.findings.filter((f) => !baseKeys.has(findingKey(f)));
    const removed = base.findings.filter((f) => !headKeys.has(findingKey(f)));
    const unchangedCount = head.findings.length - added.length;

    return NextResponse.json({
      base_ref,
      head_ref,
      base_files_scanned: base.files_scanned,
      head_files_scanned: head.files_scanned,
      added,
      removed,
      unchanged_count: unchangedCount,
    });
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : String(err) },
      { status: 502 },
    );
  }
}
