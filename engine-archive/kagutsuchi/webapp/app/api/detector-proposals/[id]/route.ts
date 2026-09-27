import { NextRequest, NextResponse } from "next/server";
import { sql, ensureDetectorProposalSchema, setDetectorProposalReview } from "@/lib/db";

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

// Two distinct things this PATCH can do, disambiguated by body:
//
//  - A JSON body of {"review": "approve"} or {"review": "reject"} is the
//    fast closed-loop review action from the /detector-proposals page's
//    Approve/Reject buttons. Approving makes the signature start being
//    sent to every scan immediately (see lib/db.ts's
//    listApprovedLearnedSignatures) - still just data (a dotted call
//    name), matched through the exact same taint-gated logic as a
//    hand-written detector, never executed code.
//  - No body (or a body without "review") is the older, slower path:
//    marks a proposal as promoted, i.e. a human has hand-written the
//    equivalent entry (plus a test) into ast_scan.py's real _SIGNATURES
//    table. Called by scripts/promote_detector.py's --confirm step -
//    never called automatically, since only a human actually editing
//    ast_scan.py knows whether that genuinely happened.
export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = await request.json().catch(() => null);
  const review = body && (body.review === "approve" || body.review === "reject") ? body.review : null;

  try {
    if (review) {
      await setDetectorProposalReview(id, review);
      return NextResponse.json({ ok: true, review });
    }
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
