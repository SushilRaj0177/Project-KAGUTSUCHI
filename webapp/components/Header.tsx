"use client";

import { useLanguage } from "./LanguageContext";
import { LanguageToggle } from "./LanguageToggle";

export function Header() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <header className="mb-10 flex items-end justify-between gap-4 border-b border-line pb-6">
      <div>
        <div className="flex items-baseline gap-3">
          <h1 className="font-display text-3xl font-extrabold tracking-wide">
            KAGU<span className="text-ember-500">TSU</span>CHI
          </h1>
          {/* Always Japanese — a fixed brand mark, not a translated string */}
          <span className="font-jp text-lg text-steel-400">鍛・検証</span>
        </div>
        <p className={`mt-1 text-sm text-steel-400 ${jp}`}>{t.tagline}</p>
      </div>
      <div className="flex items-center gap-5">
        <div className={`text-right text-xs text-steel-400 ${jp}`}>{t.logLabelEn}</div>
        <LanguageToggle />
      </div>
    </header>
  );
}
