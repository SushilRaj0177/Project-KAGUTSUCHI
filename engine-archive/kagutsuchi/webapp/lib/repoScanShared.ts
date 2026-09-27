import { listApprovedLearnedSignatures, recordDetectorProposal } from "@/lib/db";

// Shared between the synchronous scan route (analyze-repo/route.ts) and
// the async job-based one (analyze-repo/start + analyze-repo/jobs/[jobId])
// -- both need the same "which commit is this" resolution and the same
// best-effort proposal persistence, and having two copies drift apart is
// exactly how a caching bug hides.

export const GITHUB_URL_RE = /^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+?)(\.git)?\/?$/;

export interface DetectorProposal {
  class_name: string;
  call_signature: string;
  rationale: string;
  severity_hint: string;
  source_file_path: string;
}

/** Best-effort: looks up the current HEAD commit SHA of the repo's
 * default branch via GitHub's public REST API (no auth, no git binary
 * needed -- Vercel's serverless runtime doesn't ship one). Used only to
 * key the scan-result cache; any failure here just means "skip the
 * cache," never a request failure. */
export async function resolveHeadSha(owner: string, repo: string): Promise<string | null> {
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

/** Injects every approved-but-not-yet-hand-promoted detector proposal
 * into an outgoing scan request body as `learned_signatures`, so an
 * approval on /detector-proposals starts actually being checked for on
 * the very next scan - the closed loop, not just a discovery feed. Best-
 * effort: a lookup failure (e.g. DATABASE_URL not configured) just means
 * the request goes out with no learned signatures, same as before this
 * existed, never a failed scan. */
export async function withLearnedSignatures(bodyText: string): Promise<string> {
  let signatures: unknown[] = [];
  try {
    signatures = await listApprovedLearnedSignatures();
  } catch {
    return bodyText;
  }
  if (signatures.length === 0) return bodyText;
  try {
    const parsed = JSON.parse(bodyText);
    return JSON.stringify({ ...parsed, learned_signatures: signatures });
  } catch {
    return bodyText;
  }
}

/** Best-effort: never lets a persistence failure affect the scan
 * response the user actually gets. */
export async function persistProposals(proposals: unknown, repoLabel: string): Promise<void> {
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
