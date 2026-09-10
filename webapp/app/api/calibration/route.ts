import { NextResponse } from "next/server";
import { ensureSchema, sql } from "@/lib/db";

// Surfaces verification/calibration.py's research-direction-D idea
// (is the LLM's stated confidence in an attack payload trustworthy?)
// as real data from the live site, not just a library nobody can see.
//
// Honest limitation, stated plainly rather than glossed over: a row only
// ever lands in `runs` (see webapp/app/api/backend/verify/route.ts) when
// the attack against the ORIGINAL code succeeded AND a fix was proposed
// and replayed. So every hypothesis_confidence value here comes from a
// case where the model's payload actually worked - there is no negative
// (attack failed) sample in this data, because a failed attack has
// nothing to persist a "before/after/result" row for. This measures
// "was the model appropriately confident when it turned out to be
// right", not a full calibration curve with both outcomes - see the
// `note` field in the response, which the /calibration page surfaces
// directly rather than letting the numbers imply more than they show.
export async function GET() {
  try {
    await ensureSchema();
    const rows = await sql`
      SELECT hypothesis_confidence FROM runs
      WHERE hypothesis_confidence IS NOT NULL
      ORDER BY created_at ASC
    `;
    const confidences = rows.map((r) => r.hypothesis_confidence as number);

    if (confidences.length === 0) {
      return NextResponse.json({ n: 0, brier_score: null, buckets: {} });
    }

    // Every sample here is a known success (see module docstring above),
    // so the Brier score reduces to mean squared distance from 1.0 --
    // "how much did the model undersell its own correct payload."
    const brierScore = confidences.reduce((sum, c) => sum + (c - 1) ** 2, 0) / confidences.length;

    const buckets: Record<string, { n: number; mean_stated_confidence: number }> = {};
    for (const c of confidences) {
      const bucketIndex = Math.min(Math.floor(c * 10), 9);
      const label = `${bucketIndex * 10}-${bucketIndex * 10 + 10}%`;
      if (!buckets[label]) buckets[label] = { n: 0, mean_stated_confidence: 0 };
      buckets[label].n += 1;
      buckets[label].mean_stated_confidence += c;
    }
    for (const b of Object.values(buckets)) {
      b.mean_stated_confidence /= b.n;
    }

    return NextResponse.json({
      n: confidences.length,
      brier_score: brierScore,
      buckets,
      note:
        "Every sample here comes from a case where the model's attack actually succeeded " +
        "(that's a precondition for a row existing at all) - this shows whether the model " +
        "was appropriately confident when it turned out right, not a full calibration curve " +
        "including failed hypotheses.",
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not compute calibration: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
