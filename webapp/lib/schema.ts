import { z } from "zod";

// Mirrors contracts/CONTRACTS.md — kept loose (passthrough / z.record) on
// the nested objects rather than re-declaring every field, since this is
// a display surface, not a third schema to keep in sync by hand.
const jsonObject = z.record(z.string(), z.unknown());

export const IngestRunSchema = z.object({
  id: z.string().uuid(),
  fixture_name: z.string().min(1),
  sensitive_op: z.string().min(1),
  finding: jsonObject,
  hypothesis: jsonObject,
  before_evidence: jsonObject,
  after_evidence: jsonObject,
  verdict: z.enum([
    "VERIFIED_FIXED",
    "STILL_VULNERABLE",
    "FALSE_POSITIVE",
    "INCONCLUSIVE",
  ]),
  confidence: z.number().min(0).max(1),
  replay_identical: z.boolean(),
  summary: z.string().min(1),
});

export type IngestRun = z.infer<typeof IngestRunSchema>;
