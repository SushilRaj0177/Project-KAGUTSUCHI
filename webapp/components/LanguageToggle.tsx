"use client";

import { useLanguage } from "@/components/LanguageContext";

export function LanguageToggle() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="inline-flex overflow-hidden rounded border border-slate-700 text-xs">
      <button
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
        className={`px-2 py-1 transition-colors ${lang === "en" ? "bg-white text-slate-950" : "text-slate-400 hover:text-white"}`}
      >
        EN
      </button>
      <button
        onClick={() => setLang("ja")}
        aria-pressed={lang === "ja"}
        className={`font-jp px-2 py-1 transition-colors ${lang === "ja" ? "bg-white text-slate-950" : "text-slate-400 hover:text-white"}`}
      >
        日本語
      </button>
    </div>
  );
}
