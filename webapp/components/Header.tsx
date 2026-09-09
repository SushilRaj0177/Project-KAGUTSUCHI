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
        <Link href="/" className="flex items-baseline gap-3">
          <h1 className="font-display text-2xl font-extrabold tracking-wide">KAGUTSUCHI</h1>
          {/* Always Japanese — a fixed brand mark, not a translated string */}
          <span className="font-jp text-base text-steel-400">鍛・検証</span>
        </Link>
        <div className="mt-1 flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-paper-50 opacity-60 cursor-blink" />
          <p className={`text-xs tracking-wide text-steel-400 uppercase ${jp}`}>{t.tagline}</p>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <nav className={`flex items-center gap-5 text-xs tracking-wide text-steel-400 uppercase ${jp}`}>
          <Link href="/" className="transition-colors hover:text-paper-50">
            {t.navScan}
          </Link>
          <Link href="/dashboard" className="transition-colors hover:text-paper-50">
            {t.navDashboard}
          </Link>
        </nav>
        <LanguageToggle />
      </div>
    </header>
  );
}
