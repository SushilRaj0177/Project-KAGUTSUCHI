import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";
import { getCachedRepoScan } from "@/lib/db";
import { GITHUB_URL_RE, persistProposals, resolveHeadSha, withLearnedSignatures } from "@/lib/repoScanShared";

// Kicks off a repo scan as a background job on the backend and returns
// almost instantly with a job_id -- see server/jobs.py and
// server/main.py's /api/analyze-repo/start. This exists because a large
// repo's scan can take longer than a serverless route's own request
// budget allows, which is exactly what caused a live 504 (see
// webapp/app/api/backend/analyze-repo/route.ts's synchronous version,
// still used for the cache-hit fast path there and by
// /api/backend/compare-repo). The frontend polls
// /api/backend/analyze-repo/jobs/[jobId] for the result.
export const maxDuration = 15;

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const bodyText = await request.text();
  let repoUrl: string | undefined;
  try {
    repoUrl = JSON.parse(bodyText)?.repo_url;
  } catch {
    // fall through - malformed body, let the backend reject it normally
  }

  const match = typeof repoUrl === "string" ? GITHUB_URL_RE.exec(repoUrl.trim()) : null;
  const owner = match?.[1];
  const repo = match?.[2];
  const sha = owner && repo ? await resolveHeadSha(owner, repo) : null;

  if (owner && repo && sha) {
    try {
      const cached = await getCachedRepoScan(owner, repo, sha);
      if (cached) {
        await persistProposals(cached.new_detector_proposals, `${owner}/${repo}`);
        return NextResponse.json({ status: "done", cached: true, commit_sha: sha, result: cached });
      }
    } catch {
      // cache read failed (e.g. DATABASE_URL not configured) - scan for real instead of failing
    }
  }

  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/analyze-repo/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Client-IP": clientIp(request) },
      body: await withLearnedSignatures(bodyText),
    });
    const data = await upstream.text();
    if (!upstream.ok) {
      return new NextResponse(data, { status: upstream.status, headers: { "Content-Type": "application/json" } });
    }
    const parsed = JSON.parse(data);
    return NextResponse.json({ job_id: parsed.job_id, owner, repo, commit_sha: sha });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not reach backend: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
