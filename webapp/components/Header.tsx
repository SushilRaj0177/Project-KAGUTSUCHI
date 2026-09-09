"use client";

import Link from "next/link";
import { BackendStatus } from "./BackendStatus";
import { useLanguage } from "./LanguageContext";
import { LanguageToggle } from "./LanguageToggle";

export function Header() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <header className="relative z-10 mb-16 flex items-end justify-between gap-4 border-b border-line pb-6">
      <div>
        <Link data-cursor="hover" href="/" className="flex items-baseline gap-3">
          <h1 className="font-display text-2xl font-extrabold tracking-wide">
            KAGU<span className="neon-text-pink">TSU</span>CHI
          </h1>
          {/* Always Japanese — a fixed brand mark, not a translated string */}
          <span className="font-jp text-base text-steel-400">鍛・検証</span>
        </Link>
        <div className="mt-1 flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-neon-cyan shadow-[0_0_6px_var(--neon-cyan)] cursor-blink" />
          <p className={`text-xs tracking-wide text-steel-400 uppercase ${jp}`}>{t.tagline}</p>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <nav className={`flex items-center gap-5 text-xs tracking-wide text-steel-400 uppercase ${jp}`}>
          <Link data-cursor="hover" href="/" className="transition-colors hover:text-neon-cyan">
            {t.navScan}
          </Link>
          <Link data-cursor="hover" href="/dashboard" className="transition-colors hover:text-neon-cyan">
            {t.navDashboard}
          </Link>
        </nav>
        <BackendStatus />
        <LanguageToggle />
      </div>
    </header>
  );
}
