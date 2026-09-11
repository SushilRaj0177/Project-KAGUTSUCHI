import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";
import { getCachedRepoScan, setCachedRepoScan } from "@/lib/db";
import { GITHUB_URL_RE, persistProposals, resolveHeadSha, withLearnedSignatures } from "@/lib/repoScanShared";

// Proxies to the FastAPI backend server-side. Browser CORS rules only
// apply to fetch() calls made FROM the browser -- routing through our own
// Next.js server means the browser only ever talks to our own origin
// (no CORS involved at all), while this server-to-server call is exempt
// from the CORS preflight that GitHub Codespaces' port-forwarding proxy
// blocks for third-party browser origins.
//
// Kept as a synchronous, blocking call for callers that want a full
// result in one request (still used for the cache-hit fast path here,
// and directly by /api/backend/compare-repo). For the main scan UI,
// which can hit this route's own ~60s budget on a large repo (a live
// 504 - see COORDINATION.md), see analyze-repo/start + analyze-repo/jobs/
// [jobId] for the polling version.
export const maxDuration = 60;

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
        return NextResponse.json({ ...cached, cached: true, commit_sha: sha });
      }
    } catch {
      // cache read failed (e.g. DATABASE_URL not configured) - scan for real instead of failing
    }
  }

  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/analyze-repo`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Client-IP": clientIp(request) },
      body: await withLearnedSignatures(bodyText),
    });
    const data = await upstream.text();

    if (upstream.ok && owner && repo && sha) {
      try {
        const parsed = JSON.parse(data);
        await setCachedRepoScan(owner, repo, sha, parsed);
        await persistProposals(parsed.new_detector_proposals, `${owner}/${repo}`);
        return NextResponse.json({ ...parsed, commit_sha: sha }, { status: upstream.status });
      } catch {
        // best-effort cache write - never let a caching failure affect the response
      }
    }

    return new NextResponse(data, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not reach backend: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
