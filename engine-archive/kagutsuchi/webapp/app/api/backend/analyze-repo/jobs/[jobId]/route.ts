import { NextRequest, NextResponse } from "next/server";
import { setCachedRepoScan } from "@/lib/db";
import { persistProposals } from "@/lib/repoScanShared";

// Proxies to the backend's job-status endpoint (see server/main.py's
// GET /api/analyze-repo/jobs/{job_id}). The frontend polls this every
// couple of seconds after a POST to analyze-repo/start. On the first
// poll that comes back "done," this also does the same cache-write and
// proposal-persistence the old synchronous route did inline -- owner,
// repo, and commit_sha come back from analyze-repo/start's response, so
// the frontend passes them through as query params here.
export const maxDuration = 15;

export async function GET(request: NextRequest, { params }: { params: Promise<{ jobId: string }> }) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }
  const { jobId } = await params;
  const { searchParams } = new URL(request.url);
  const owner = searchParams.get("owner");
  const repo = searchParams.get("repo");
  const sha = searchParams.get("sha");

  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/analyze-repo/jobs/${jobId}`);
    if (!upstream.ok) {
      const data = await upstream.text();
      return new NextResponse(data, { status: upstream.status, headers: { "Content-Type": "application/json" } });
    }
    const body = await upstream.json();

    if (body.status === "done" && body.result) {
      if (owner && repo && sha) {
        try {
          await setCachedRepoScan(owner, repo, sha, body.result);
        } catch {
          // best-effort cache write - never let a caching failure affect the response
        }
      }
      await persistProposals(body.result.new_detector_proposals, owner && repo ? `${owner}/${repo}` : "unknown");
      return NextResponse.json({ status: "done", result: { ...body.result, commit_sha: sha ?? undefined } });
    }

    return NextResponse.json(body);
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not reach backend: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
