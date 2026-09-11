import { NextRequest, NextResponse } from "next/server";
import { ensureSchema, sql, type RunRow } from "@/lib/db";
import { IngestRunSchema } from "@/lib/schema";

const RUN_LIMIT = 100;

export async function GET() {
  try {
    await ensureSchema();
    const rows = (await sql`
      SELECT id, created_at, fixture_name, sensitive_op, finding, hypothesis,
             before_evidence, after_evidence, verdict, confidence,
             replay_identical, summary, hypothesis_confidence
      FROM runs
      ORDER BY created_at DESC
      LIMIT ${RUN_LIMIT}
    `) as RunRow[];
    return NextResponse.json({ runs: rows });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not load runs: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}

export async function POST(request: NextRequest) {
  const apiKey = request.headers.get("x-api-key");
  if (!process.env.INGEST_API_KEY || apiKey !== process.env.INGEST_API_KEY) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const body = await request.json().catch(() => null);
  const parsed = IngestRunSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "invalid payload", issues: parsed.error.issues },
      { status: 400 },
    );
  }
  const run = parsed.data;

  await ensureSchema();
  await sql`
    INSERT INTO runs (
      id, fixture_name, sensitive_op, finding, hypothesis,
      before_evidence, after_evidence, verdict, confidence,
      replay_identical, summary
    ) VALUES (
      ${run.id}, ${run.fixture_name}, ${run.sensitive_op},
      ${JSON.stringify(run.finding)}, ${JSON.stringify(run.hypothesis)},
      ${JSON.stringify(run.before_evidence)}, ${JSON.stringify(run.after_evidence)},
      ${run.verdict}, ${run.confidence}, ${run.replay_identical}, ${run.summary}
    )
    ON CONFLICT (id) DO NOTHING
  `;

  return NextResponse.json({ ok: true, id: run.id }, { status: 201 });
}
