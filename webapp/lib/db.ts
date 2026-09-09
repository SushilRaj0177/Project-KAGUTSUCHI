import { neon, type NeonQueryFunction } from "@neondatabase/serverless";

// Vercel's Postgres storage integration (Neon-backed) injects this env var
// automatically once added to the project in the Vercel dashboard. No
// manual schema setup needed — ensureSchema() below creates the table on
// first use. Lazily constructed: importing this module (e.g. at build
// time, when collecting page data) must not require the env var to be
// set — only actually querying does.
let cachedSql: NeonQueryFunction<false, false> | null = null;

function getSql(): NeonQueryFunction<false, false> {
  if (!cachedSql) {
    const DATABASE_URL = process.env.DATABASE_URL ?? process.env.POSTGRES_URL;
    if (!DATABASE_URL) {
      throw new Error(
        "DATABASE_URL is not set. Add the Postgres storage integration to this " +
          "Vercel project (Storage -> Connect Store -> Postgres), or set " +
          "DATABASE_URL locally in .env.local for development.",
      );
    }
    cachedSql = neon(DATABASE_URL);
  }
  return cachedSql;
}

export const sql: NeonQueryFunction<false, false> = ((...args: Parameters<NeonQueryFunction<false, false>>) =>
  getSql()(...args)) as NeonQueryFunction<false, false>;

let schemaReady: Promise<void> | null = null;

/** Idempotent — safe to call on every request. Only actually runs the
 * DDL once per cold start, then reuses the same resolved promise. */
export function ensureSchema(): Promise<void> {
  if (!schemaReady) {
    schemaReady = sql`
      CREATE TABLE IF NOT EXISTS runs (
        id UUID PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        fixture_name TEXT NOT NULL,
        sensitive_op TEXT NOT NULL,
        finding JSONB NOT NULL,
        hypothesis JSONB NOT NULL,
        before_evidence JSONB NOT NULL,
        after_evidence JSONB NOT NULL,
        verdict TEXT NOT NULL,
        confidence DOUBLE PRECISION NOT NULL,
        replay_identical BOOLEAN NOT NULL,
        summary TEXT NOT NULL
      )
    `.then(() => undefined);
  }
  return schemaReady;
}

export type RunRow = {
  id: string;
  created_at: string;
  fixture_name: string;
  sensitive_op: string;
  finding: Record<string, unknown>;
  hypothesis: Record<string, unknown>;
  before_evidence: Record<string, unknown>;
  after_evidence: Record<string, unknown>;
  verdict: string;
  confidence: number;
  replay_identical: boolean;
  summary: string;
};
