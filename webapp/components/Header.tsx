"use client";

import Link from "next/link";
import { useLanguage } from "./LanguageContext";
import { LanguageToggle } from "./LanguageToggle";

export function Header() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <header className="mb-16 flex items-end justify-between gap-4 border-b border-line pb-6">
      <div>
        <Link data-cursor="hover" href="/" className="flex items-baseline gap-3">
          <h1 className="font-display text-2xl font-extrabold tracking-wide">
            KAGU<span className="text-seal-500">TSU</span>CHI
          </h1>
          {/* Always Japanese — a fixed brand mark, not a translated string */}
          <span className="font-jp text-base text-steel-400">鍛・検証</span>
        </Link>
        <div className="mt-1 flex items-center gap-2">
          <span className="bg-seal-500 h-1.5 w-1.5 rounded-full seal-pulse" />
          <p className={`text-xs tracking-wide text-steel-400 uppercase ${jp}`}>{t.tagline}</p>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <nav className={`flex items-center gap-5 text-xs tracking-wide text-steel-400 uppercase ${jp}`}>
          <Link data-cursor="hover" href="/" className="transition-colors hover:text-seal-500">
            {t.navScan}
          </Link>
          <Link data-cursor="hover" href="/dashboard" className="transition-colors hover:text-seal-500">
            {t.navDashboard}
          </Link>
        </nav>
        <LanguageToggle />
      </div>
    </header>
  );
}
