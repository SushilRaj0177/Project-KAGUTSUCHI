import { Header } from "@/components/Header";
import { RepoScanner } from "@/components/RepoScanner";

export default function ScanPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />
      <RepoScanner />
    </main>
  );
}
