"use client";

import { useLanguage } from "./LanguageContext";

export function LanguageToggle() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="inline-flex border border-line-strong text-xs font-semibold">
      <button
        data-cursor="hover"
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
        className={`px-3 py-1.5 transition-colors ${
          lang === "en" ? "bg-neon-cyan text-void-950" : "text-steel-400 hover:text-paper-50"
        }`}
      >
        EN
      </button>
      <button
        data-cursor="hover"
        onClick={() => setLang("ja")}
        aria-pressed={lang === "ja"}
        className={`font-jp px-3 py-1.5 transition-colors ${
          lang === "ja" ? "bg-neon-cyan text-void-950" : "text-steel-400 hover:text-paper-50"
        }`}
      >
        日本語
      </button>
    </div>
  );
}
