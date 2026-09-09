"use client";

import { useLanguage } from "./LanguageContext";

export function LanguageToggle() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="inline-flex border border-line-strong text-xs font-semibold">
      <button
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
        className={`px-3 py-1.5 transition-colors ${
          lang === "en" ? "bg-seal-500 text-ink-950" : "text-steel-400 hover:text-paper-50"
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLang("ja")}
        aria-pressed={lang === "ja"}
        className={`font-jp px-3 py-1.5 transition-colors ${
          lang === "ja" ? "bg-seal-500 text-ink-950" : "text-steel-400 hover:text-paper-50"
        }`}
      >
        日本語
      </button>
    </div>
  );
}
