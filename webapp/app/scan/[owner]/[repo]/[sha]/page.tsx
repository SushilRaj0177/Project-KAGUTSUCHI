import { use } from "react";

// Placeholder only - see webapp/app/page.tsx.
export default function ScanPermalinkPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string; sha: string }>;
}) {
  const { owner, repo, sha } = use(params);
  return (
    <main className="p-8">
      <p>
        Scan permalink for {owner}/{repo}@{sha} — front-end rebuild in progress.
      </p>
    </main>
  );
}
