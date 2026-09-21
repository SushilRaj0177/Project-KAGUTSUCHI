"use client";

import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { useLanguage } from "@/components/LanguageContext";

export default function NotFound() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <SiteNav />

        <div className="mt-24 text-center">
          <p className="font-mono text-xs tracking-widest text-slate-600 uppercase">{t.notFoundEyebrow}</p>
          <h1 className={`mt-3 text-3xl font-bold sm:text-4xl ${jp}`}>{t.notFoundTitle}</h1>
          <p className={`mt-3 text-slate-400 ${jp}`}>{t.notFoundBody}</p>
          <Link
            href="/scan"
            className={`mt-8 inline-block rounded bg-white px-6 py-3 text-sm font-semibold text-slate-950 transition-transform hover:scale-105 ${jp}`}
          >
            {t.notFoundCta}
          </Link>
        </div>
      </div>
    </main>
  );
}
