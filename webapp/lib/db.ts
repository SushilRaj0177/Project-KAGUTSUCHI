import { randomUUID } from "crypto";
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
    schemaReady = (async () => {
      await sql`
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
      `;
      // Added later, for verification/calibration.py's research-direction-D
      // work: the LLM's own stated pre-attack confidence that its payload
      // would succeed. Deliberately a DIFFERENT column from `confidence`
      // above, which is VerificationResult's own (currently always 1.0,
      // deterministic) verdict confidence -- conflating the two would
      // silently corrupt calibration data with an unrelated number.
      // Nullable: most existing rows predate this column, and any row
      // whose stated confidence didn't parse also has no value to store.
      await sql`ALTER TABLE runs ADD COLUMN IF NOT EXISTS hypothesis_confidence DOUBLE PRECISION`;
    })();
  }
  return schemaReady;
}

let repoScanSchemaReady: Promise<void> | null = null;

/** Caches a completed /analyze-repo response by (owner, repo, commit sha)
 * so re-scanning the exact same commit of a popular demo repo (flask,
 * django, pygoat) is instant on a second visit instead of re-cloning and
 * re-scanning (including the LLM pass) from scratch. Keyed on the real
 * commit SHA, not just owner/repo, so a cache hit can never serve stale
 * results for a repo that's since been pushed to. */
export function ensureRepoScanCacheSchema(): Promise<void> {
  if (!repoScanSchemaReady) {
    repoScanSchemaReady = sql`
      CREATE TABLE IF NOT EXISTS repo_scan_cache (
        owner TEXT NOT NULL,
        repo TEXT NOT NULL,
        commit_sha TEXT NOT NULL,
        response JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (owner, repo, commit_sha)
      )
    `.then(() => undefined);
  }
  return repoScanSchemaReady;
}

export async function getCachedRepoScan(
  owner: string,
  repo: string,
  commitSha: string,
): Promise<Record<string, unknown> | null> {
  await ensureRepoScanCacheSchema();
  const rows = await sql`
    SELECT response FROM repo_scan_cache
    WHERE owner = ${owner} AND repo = ${repo} AND commit_sha = ${commitSha}
    LIMIT 1
  `;
  return rows.length > 0 ? (rows[0].response as Record<string, unknown>) : null;
}

export async function setCachedRepoScan(
  owner: string,
  repo: string,
  commitSha: string,
  response: Record<string, unknown>,
): Promise<void> {
  await ensureRepoScanCacheSchema();
  await sql`
    INSERT INTO repo_scan_cache (owner, repo, commit_sha, response)
    VALUES (${owner}, ${repo}, ${commitSha}, ${JSON.stringify(response)})
    ON CONFLICT (owner, repo, commit_sha) DO NOTHING
  `;
}

/** Most recent scan of any commit of (owner, repo) -- backs the
 * shields.io-style embeddable badge, which reflects "last known state",
 * not one pinned commit the way the permalink page does. */
export async function getLatestRepoScan(
  owner: string,
  repo: string,
): Promise<{ response: Record<string, unknown>; created_at: string } | null> {
  await ensureRepoScanCacheSchema();
  const rows = await sql`
    SELECT response, created_at FROM repo_scan_cache
    WHERE owner = ${owner} AND repo = ${repo}
    ORDER BY created_at DESC
    LIMIT 1
  `;
  return rows.length > 0
    ? { response: rows[0].response as Record<string, unknown>, created_at: rows[0].created_at as string }
    : null;
}

let detectorProposalSchemaReady: Promise<void> | null = null;

/** Candidate NEW deterministic detectors, discovered by the LLM scan
 * (system/analysis/llm_scan.py) finding a vulnerability pattern outside
 * ast_scan.py's fixed category list -- see that module's docstring for
 * why a proposal is advisory only, never auto-applied to the real
 * _SIGNATURES table. This is purely the discovery/aggregation side: a
 * human (or a session) reviews these on /detector-proposals and
 * manually promotes one via scripts/promote_detector.py. */
export function ensureDetectorProposalSchema(): Promise<void> {
  if (!detectorProposalSchemaReady) {
    detectorProposalSchemaReady = sql`
      CREATE TABLE IF NOT EXISTS detector_proposals (
        id UUID PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        class_name TEXT NOT NULL,
        call_signature TEXT NOT NULL,
        rationale TEXT NOT NULL,
        severity_hint TEXT NOT NULL,
        source_file_path TEXT NOT NULL,
        source_repo TEXT,
        times_seen INTEGER NOT NULL DEFAULT 1,
        promoted BOOLEAN NOT NULL DEFAULT false
      )
    `.then(() => undefined);
  }
  return detectorProposalSchemaReady;
}

export type DetectorProposalRow = {
  id: string;
  created_at: string;
  class_name: string;
  call_signature: string;
  rationale: string;
  severity_hint: string;
  source_file_path: string;
  source_repo: string | null;
  times_seen: number;
  promoted: boolean;
};

/** Upsert-by-signature: the same (class_name, call_signature) pair
 * proposed again just bumps times_seen instead of creating a duplicate
 * row - a class the model keeps independently rediscovering across
 * different scans is a stronger signal than one proposed once. */
export async function recordDetectorProposal(proposal: {
  class_name: string;
  call_signature: string;
  rationale: string;
  severity_hint: string;
  source_file_path: string;
  source_repo?: string;
}): Promise<void> {
  await ensureDetectorProposalSchema();
  const existing = await sql`
    SELECT id FROM detector_proposals
    WHERE class_name = ${proposal.class_name} AND call_signature = ${proposal.call_signature}
    LIMIT 1
  `;
  if (existing.length > 0) {
    await sql`UPDATE detector_proposals SET times_seen = times_seen + 1 WHERE id = ${existing[0].id}`;
    return;
  }
  await sql`
    INSERT INTO detector_proposals (
      id, class_name, call_signature, rationale, severity_hint, source_file_path, source_repo
    ) VALUES (
      ${randomUUID()}, ${proposal.class_name}, ${proposal.call_signature}, ${proposal.rationale},
      ${proposal.severity_hint}, ${proposal.source_file_path}, ${proposal.source_repo ?? null}
    )
  `;
}

export async function listDetectorProposals(): Promise<DetectorProposalRow[]> {
  await ensureDetectorProposalSchema();
  const rows = await sql`
    SELECT * FROM detector_proposals WHERE promoted = false ORDER BY times_seen DESC, created_at DESC
  `;
  return rows as DetectorProposalRow[];
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
  hypothesis_confidence: number | null;
  replay_identical: boolean;
  summary: string;
};
