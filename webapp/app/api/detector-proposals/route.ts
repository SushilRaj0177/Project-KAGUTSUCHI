import { NextResponse } from "next/server";
import { listDetectorProposals } from "@/lib/db";

// Read-only listing for the /detector-proposals page. See
// system/analysis/llm_scan.py's docstring for why these are advisory
// (never auto-applied to ast_scan.py's real _SIGNATURES table) and
// scripts/promote_detector.py for the reviewed path to actually add one.
export async function GET() {
  try {
    const proposals = await listDetectorProposals();
    return NextResponse.json({ proposals });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not read detector proposals: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
