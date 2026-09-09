import { Dashboard } from "@/components/Dashboard";
import { Header } from "@/components/Header";
import { ensureSchema, sql, type RunRow } from "@/lib/db";

export const dynamic = "force-dynamic";

async function getRuns(): Promise<RunRow[]> {
  await ensureSchema();
  return (await sql`
    SELECT id, created_at, fixture_name, sensitive_op, finding, hypothesis,
           before_evidence, after_evidence, verdict, confidence,
           replay_identical, summary
    FROM runs
    ORDER BY created_at DESC
    LIMIT 100
  `) as RunRow[];
}

export default async function Home() {
  const runs = await getRuns();

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />
      <Dashboard runs={runs} />
    </main>
  );
}
