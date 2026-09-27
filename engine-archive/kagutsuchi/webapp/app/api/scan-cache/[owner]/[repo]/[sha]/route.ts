import { NextResponse } from "next/server";
import { getCachedRepoScan } from "@/lib/db";

// Backs the shareable permalink pages at /scan/[owner]/[repo]/[sha] --
// read-only lookup into the same repo_scan_cache table analyze-repo
// writes to. A permalink only ever resolves if that exact commit was
// actually scanned before (via the live site or another visitor sharing
// the link first) -- there's no re-scan-on-demand here, since that would
// let a permalink URL itself become a way to trigger an unbounded scan.
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ owner: string; repo: string; sha: string }> },
) {
  const { owner, repo, sha } = await params;
  try {
    const cached = await getCachedRepoScan(owner, repo, sha);
    if (!cached) {
      return NextResponse.json({ detail: "No cached scan for this repo + commit" }, { status: 404 });
    }
    return NextResponse.json({ ...cached, cached: true, commit_sha: sha });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not read scan cache: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
