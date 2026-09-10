import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";
import { getCachedRepoScan, recordDetectorProposal, setCachedRepoScan } from "@/lib/db";

// Proxies to the FastAPI backend server-side. Browser CORS rules only
// apply to fetch() calls made FROM the browser -- routing through our own
// Next.js server means the browser only ever talks to our own origin
// (no CORS involved at all), while this server-to-server call is exempt
// from the CORS preflight that GitHub Codespaces' port-forwarding proxy
// blocks for third-party browser origins.
export const maxDuration = 60;

const GITHUB_URL_RE = /^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+?)(\.git)?\/?$/;

// Best-effort: looks up the current HEAD commit SHA of the repo's default
// branch via GitHub's public REST API (no auth, no git binary needed --
// Vercel's serverless runtime doesn't ship one). Used only to key the
// scan-result cache; any failure here (rate-limited, private repo,
// network hiccup) just means "skip the cache," never a request failure.
async function resolveHeadSha(owner: string, repo: string): Promise<string | null> {
  try {
    const repoRes = await fetch(`https://api.github.com/repos/${owner}/${repo}`, {
      signal: AbortSignal.timeout(5000),
    });
    if (!repoRes.ok) return null;
    const repoJson = await repoRes.json();
    const branch = repoJson.default_branch;
    if (typeof branch !== "string") return null;

    const commitRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/commits/${branch}`, {
      signal: AbortSignal.timeout(5000),
      headers: { Accept: "application/vnd.github.sha" },
    });
    if (!commitRes.ok) return null;
    const sha = (await commitRes.text()).trim();
    return /^[0-9a-f]{40}$/.test(sha) ? sha : null;
  } catch {
    return null;
  }
}

interface DetectorProposal {
  class_name: string;
  call_signature: string;
  rationale: string;
  severity_hint: string;
  source_file_path: string;
}

// Best-effort: never lets a persistence failure affect the scan response
// the user actually gets, same pattern as setCachedRepoScan below.
async function persistProposals(proposals: unknown, repoLabel: string): Promise<void> {
  if (!Array.isArray(proposals)) return;
  for (const p of proposals) {
    if (
      p &&
      typeof p === "object" &&
      typeof (p as DetectorProposal).class_name === "string" &&
      typeof (p as DetectorProposal).call_signature === "string"
    ) {
      try {
        await recordDetectorProposal({ ...(p as DetectorProposal), source_repo: repoLabel });
      } catch {
        // swallow - see function docstring
      }
    }
  }
}

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
      body: bodyText,
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
