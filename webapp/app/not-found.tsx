import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <SiteNav />

        <div className="mt-24 text-center">
          <p className="font-mono text-xs tracking-widest text-slate-600 uppercase">404</p>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Nothing here.</h1>
          <p className="mt-3 text-slate-400">
            This page doesn&apos;t exist — or a scan permalink pointed at a commit that was never scanned.
          </p>
          <Link
            href="/scan"
            className="mt-8 inline-block rounded bg-white px-6 py-3 text-sm font-semibold text-slate-950 transition-transform hover:scale-105"
          >
            Run a scan →
          </Link>
        </div>
      </div>
    </main>
  );
}
