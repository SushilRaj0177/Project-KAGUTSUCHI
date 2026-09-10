import { NextResponse } from "next/server";
import { sql, ensureDetectorProposalSchema } from "@/lib/db";

// Single-proposal lookup, used by scripts/promote_detector.py so the
// promotion tool can work from just a proposal id (as shown on the
// /detector-proposals page) without needing direct database credentials.
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    await ensureDetectorProposalSchema();
    const rows = await sql`SELECT * FROM detector_proposals WHERE id = ${id} LIMIT 1`;
    if (rows.length === 0) {
      return NextResponse.json({ detail: "No such proposal" }, { status: 404 });
    }
    return NextResponse.json(rows[0]);
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not read proposal: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}

// Marks a proposal as promoted (i.e. it has already been manually added
// to ast_scan.py's real _SIGNATURES table by a human/session) so it drops
// off the pending list on /detector-proposals. Called by
// scripts/promote_detector.py's --confirm step - never called
// automatically, since only a human actually editing ast_scan.py knows
// whether promotion genuinely happened.
export async function PATCH(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    await ensureDetectorProposalSchema();
    await sql`UPDATE detector_proposals SET promoted = true WHERE id = ${id}`;
    return NextResponse.json({ ok: true });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not update proposal: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
