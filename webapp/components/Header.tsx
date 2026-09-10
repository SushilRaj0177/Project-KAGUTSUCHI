"use client";

import Link from "next/link";
import { BackendStatus } from "./BackendStatus";
import { useLanguage } from "./LanguageContext";
import { LanguageToggle } from "./LanguageToggle";

export function Header() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <header className="relative z-10 mb-12 border-b border-line pb-5">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <Link data-cursor="hover" href="/" className="flex items-baseline gap-3">
          <h1 className="font-display text-2xl font-extrabold tracking-wide">
            KAGU<span className="neon-text-cyan">TSU</span>CHI
          </h1>
          {/* Always Japanese — a fixed brand mark, not a translated string */}
          <span className="font-jp hidden text-base text-steel-400 sm:inline">鍛・検証</span>
        </Link>

        <div className="flex items-center gap-4">
          <BackendStatus />
          <LanguageToggle />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-neon-cyan cursor-blink" />
          <p className={`text-xs tracking-wide text-steel-400 uppercase ${jp}`}>{t.tagline}</p>
        </div>

        <nav className={`flex flex-wrap items-center gap-x-5 gap-y-1 text-xs tracking-wide text-steel-400 uppercase ${jp}`}>
          <Link data-cursor="hover" href="/" className="whitespace-nowrap transition-colors hover:text-neon-cyan">
            {t.navScan}
          </Link>
          <Link data-cursor="hover" href="/dashboard" className="whitespace-nowrap transition-colors hover:text-neon-cyan">
            {t.navDashboard}
          </Link>
          <Link data-cursor="hover" href="/compare" className="whitespace-nowrap transition-colors hover:text-neon-cyan">
            {t.navCompare}
          </Link>
          <Link data-cursor="hover" href="/calibration" className="whitespace-nowrap transition-colors hover:text-neon-cyan">
            {t.navCalibration}
          </Link>
          <Link data-cursor="hover" href="/detector-proposals" className="whitespace-nowrap transition-colors hover:text-neon-cyan">
            {t.navDetectorProposals}
          </Link>
        </nav>
      </div>
    </header>
  );
}
