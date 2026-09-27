"use client";

import Link from "next/link";
import { NetworkCanvas } from "@/components/NetworkCanvas";
import { TerminalLog } from "@/components/TerminalLog";
import { SiteNav } from "@/components/SiteNav";
import { LiveCounter } from "@/components/ornament";
import { useLanguage } from "@/components/LanguageContext";

// Homepage, rebuilt again after the typography/instrument-panel
// direction was rejected outright ("looks so bad," "abandon the vibe").
// This drops that whole approach -- no ornament frame, no glitch text,
// no torn-paper panels -- in favor of a plain dark page whose dynamism
// comes from an actual live simulation (NetworkCanvas: nodes get
// flagged, attacked, and verified in real time, exactly mirroring what
// the product does) plus a live-typing event log and a ticking
// counter, rather than from a designed static composition.
export default function HomePage() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <main className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <NetworkCanvas className="absolute inset-0 h-full w-full" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-950/40 via-slate-950/10 to-slate-950" />

      <div className="relative mx-auto flex min-h-screen max-w-5xl flex-col px-6 py-8 sm:px-10">
        <SiteNav />

        <div className="flex flex-1 flex-col justify-center py-16">
          <p className={`mb-3 font-mono text-xs tracking-widest text-slate-500 uppercase ${jp}`}>
            <LiveCounter from={41862} /> {t.homeStatLabel}
          </p>
          <h1 className={`max-w-2xl text-5xl leading-tight font-bold sm:text-6xl ${jp}`}>
            {t.homeHeadline1} {t.homeHeadline2} {t.homeHeadline3}
          </h1>
          <p className={`mt-6 max-w-lg text-slate-400 ${jp}`}>{t.homeSubtitle}</p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              href="/scan"
              className={`rounded bg-white px-6 py-3 text-sm font-semibold text-slate-950 transition-transform hover:scale-105 ${jp}`}
            >
              {t.homeCtaScan}
            </Link>
            <Link
              href="/dashboard"
              className={`rounded border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-200 transition-colors hover:border-slate-500 ${jp}`}
            >
              {t.homeCtaLiveRuns}
            </Link>
          </div>

          <TerminalLog className="mt-14 max-w-md rounded border border-slate-800 bg-slate-950/70 p-4 backdrop-blur-sm" />
        </div>

        <footer className={`flex flex-wrap justify-between gap-2 border-t border-slate-800 py-6 text-xs text-slate-500 ${jp}`}>
          <span>{t.homeFooterTagline}</span>
          <span>© Kagutsuchi</span>
        </footer>
      </div>
    </main>
  );
}
