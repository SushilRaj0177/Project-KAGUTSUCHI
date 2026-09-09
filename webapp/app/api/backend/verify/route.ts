import { randomUUID } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { ensureSchema, sql } from "@/lib/db";

// See app/api/backend/analyze-repo/route.ts for why this proxy exists.
export const maxDuration = 60;

interface VerifyBackendResponse {
  finding: { file_path?: string; sensitive_op?: string; symbol?: string };
  hypothesis: Record<string, unknown>;
  before: Record<string, unknown>;
  after: Record<string, unknown> | null;
  result: { verdict: string; confidence: number; replay_identical: boolean; summary: string } | null;
  fixed_source: string | null;
  fix_error: string | null;
}

/** Best-effort: a real website Attack & Verify that reaches a full verdict
 * (before + after + result all present) is persisted to the same `runs`
 * table the CLI's publish_result.py writes to, so /dashboard becomes a
 * genuine live feed of real usage, not only CLI-fixture demos. Never lets
 * a persistence failure affect the response the user actually gets. */
async function persistIfComplete(data: VerifyBackendResponse) {
  if (!data.after || !data.result) return;
  try {
    await ensureSchema();
    await sql`
      INSERT INTO runs (
        id, fixture_name, sensitive_op, finding, hypothesis,
        before_evidence, after_evidence, verdict, confidence,
        replay_identical, summary
      ) VALUES (
        ${randomUUID()}, ${data.finding.file_path ?? "uploaded"}, ${data.finding.sensitive_op ?? "unknown"},
        ${JSON.stringify(data.finding)}, ${JSON.stringify(data.hypothesis)},
        ${JSON.stringify(data.before)}, ${JSON.stringify(data.after)},
        ${data.result.verdict}, ${data.result.confidence},
        ${data.result.replay_identical}, ${data.result.summary}
      )
    `;
  } catch {
    // No DATABASE_URL configured, or a transient DB error -- the live
    // Attack & Verify response to the user matters more than the
    // dashboard write, so this is swallowed rather than surfaced.
  }
}

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const body = await request.text();
  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const data = await upstream.text();

    if (upstream.ok) {
      const parsed = JSON.parse(data) as VerifyBackendResponse;
      await persistIfComplete(parsed);
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
