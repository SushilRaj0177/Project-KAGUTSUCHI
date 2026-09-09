import { Dashboard } from "@/components/Dashboard";
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
      <header className="mb-10 flex items-end justify-between gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-baseline gap-3">
            <h1 className="font-display text-3xl font-extrabold tracking-wide">
              KAGU<span className="text-ember-500">TSU</span>CHI
            </h1>
            <span className="font-jp text-lg text-steel-400">鍛・検証</span>
          </div>
          <p className="mt-1 text-sm text-steel-400">
            Autonomous code integrity verification — proof, not opinion.
          </p>
        </div>
        <div className="text-right text-xs text-steel-400">
          <div className="font-jp text-sm text-paper-50">検証ログ</div>
          <div>Verification Log</div>
        </div>
      </header>

      <Dashboard runs={runs} />
    </main>
  );
}
