"use client";

import Link from "next/link";
import { Header } from "./Header";
import { Marquee } from "./Marquee";
import { useLanguage } from "./LanguageContext";

function StatTile({ value, label }: { value: string; label: string }) {
  const { lang } = useLanguage();
  return (
    <div className="border border-line bg-void-900/60 p-5">
      <div className="font-display neon-text-cyan text-3xl font-extrabold tabular-nums">{value}</div>
      <div className={`mt-1 text-[11px] tracking-wide text-steel-400 uppercase ${lang === "ja" ? "font-jp normal-case" : ""}`}>
        {label}
      </div>
    </div>
  );
}

function FeatureRow({
  kanji,
  title,
  body,
  index,
}: {
  kanji: string;
  title: string;
  body: string;
  index: number;
}) {
  return (
    <div className="grid gap-4 border-t border-line py-8 first:border-t-0 md:grid-cols-[auto_1fr] md:gap-10">
      <div
        className={`font-jp text-5xl leading-none font-bold ${index % 2 === 0 ? "text-neon-cyan/25" : "text-neon-pink/25"}`}
        aria-hidden="true"
      >
        {kanji}
      </div>
      <div>
        <h3 className="font-display text-xl font-extrabold text-paper-50">{title}</h3>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-steel-400">{body}</p>
      </div>
    </div>
  );
}

function FlowStep({ n, text, isLast }: { n: number; text: string; isLast: boolean }) {
  return (
    <div className="flex gap-5">
      <div className="flex flex-col items-center">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-neon-cyan/40 bg-void-900 font-display text-base font-bold text-neon-cyan-soft">
          {n}
        </span>
        {!isLast && <span className="mt-1 w-px flex-1 bg-line-strong" />}
      </div>
      <p className="max-w-xl pb-10 text-sm leading-relaxed text-paper-50">{text}</p>
    </div>
  );
}

export function LandingPage() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Header />

      {/* Hero */}
      <section className="py-10 md:py-16">
        <div className={`inline-flex items-center gap-2 border border-line-strong px-3 py-1.5 font-mono text-[11px] tracking-wide text-steel-400 uppercase ${jp}`}>
          <span className="h-1.5 w-1.5 rounded-full bg-neon-cyan cursor-blink" />
          {t.landingBadge}
        </div>

        <h1 className={`font-display mt-6 max-w-3xl text-5xl leading-[1.05] font-extrabold tracking-tight text-paper-50 md:text-7xl ${jp}`}>
          {t.landingTitleLine1} <span className="neon-text-pink">{t.landingTitleLine1Accent}</span>
          <br />
          {t.landingTitleLine2} <span className="neon-text-cyan">{t.landingTitleLine2Accent}</span>
        </h1>

        <p className={`mt-6 max-w-xl text-sm leading-relaxed text-steel-400 ${jp}`}>{t.landingSubtitle}</p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            data-cursor="hover"
            href="/scan"
            className={`neon-border-pink border border-neon-pink bg-neon-pink/5 px-5 py-2.5 font-mono text-xs font-bold tracking-wide text-neon-pink-soft uppercase transition-colors hover:bg-neon-pink/15 ${jp}`}
          >
            {t.landingCtaScan}
          </Link>
          <Link
            data-cursor="hover"
            href="/dashboard"
            className={`border border-line-strong px-5 py-2.5 font-mono text-xs font-bold tracking-wide text-steel-400 uppercase transition-colors hover:border-neon-cyan hover:text-neon-cyan ${jp}`}
          >
            {t.landingCtaDashboard}
          </Link>
        </div>

        <div className="mt-12 grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatTile value={t.landingStat1Value} label={t.landingStat1Label} />
          <StatTile value={t.landingStat2Value} label={t.landingStat2Label} />
          <StatTile value={t.landingStat3Value} label={t.landingStat3Label} />
          <StatTile value={t.landingStat4Value} label={t.landingStat4Label} />
        </div>
      </section>

      <Marquee text="KAGUTSUCHI — " />

      {/* What the name means */}
      <section className="border-b border-line py-16">
        <div className={`font-mono text-xs font-bold tracking-widest text-neon-pink-soft uppercase ${jp}`}>
          {t.nameEyebrow}
        </div>
        <h2 className={`font-display mt-3 max-w-2xl text-3xl font-extrabold text-paper-50 md:text-4xl ${jp}`}>
          {t.nameTitle}
        </h2>
        <div className="mt-6 max-w-2xl space-y-4 text-sm leading-relaxed text-steel-400">
          <p>{t.nameBodyPart1}</p>
          <p>{t.nameBodyPart2}</p>
          <p className="text-paper-50">{t.nameBodyPart3}</p>
        </div>
      </section>

      {/* Features */}
      <section className="border-b border-line py-16">
        <div className={`font-mono text-xs font-bold tracking-widest text-neon-cyan-soft uppercase ${jp}`}>
          {t.featuresEyebrow}
        </div>
        <h2 className={`font-display mt-3 max-w-2xl text-3xl font-extrabold text-paper-50 md:text-4xl ${jp}`}>
          {t.featuresTitle}
        </h2>
        <p className={`mt-3 max-w-xl text-sm text-steel-400 ${jp}`}>{t.featuresSubtitle}</p>

        <div className="mt-8">
          <FeatureRow index={0} kanji={t.feature1Kanji} title={t.feature1Title} body={t.feature1Body} />
          <FeatureRow index={1} kanji={t.feature2Kanji} title={t.feature2Title} body={t.feature2Body} />
          <FeatureRow index={2} kanji={t.feature3Kanji} title={t.feature3Title} body={t.feature3Body} />
          <FeatureRow index={3} kanji={t.feature4Kanji} title={t.feature4Title} body={t.feature4Body} />
        </div>
      </section>

      {/* The flow */}
      <section className="py-16">
        <div className={`font-mono text-xs font-bold tracking-widest text-neon-pink-soft uppercase ${jp}`}>
          {t.flowEyebrow}
        </div>
        <h2 className={`font-display mt-3 max-w-2xl text-3xl font-extrabold text-paper-50 md:text-4xl ${jp}`}>
          {t.flowTitle}
        </h2>
        <p className={`mt-3 max-w-xl font-mono text-sm text-steel-400 ${jp}`}>{t.flowSubtitle}</p>

        <div className="mt-10">
          <FlowStep n={1} text={t.flowStep1} isLast={false} />
          <FlowStep n={2} text={t.flowStep2} isLast={false} />
          <FlowStep n={3} text={t.flowStep3} isLast={false} />
          <FlowStep n={4} text={t.flowStep4} isLast={true} />
        </div>
      </section>

      {/* Footer CTA */}
      <section className="hud-frame border border-line-strong bg-void-900/60 px-8 py-12 text-center">
        <h2 className={`font-display text-2xl font-extrabold text-paper-50 md:text-3xl ${jp}`}>
          {t.landingFooterTitle}
        </h2>
        <Link
          data-cursor="hover"
          href="/scan"
          className={`neon-border-pink mt-6 inline-block border border-neon-pink bg-neon-pink/5 px-6 py-2.5 font-mono text-xs font-bold tracking-wide text-neon-pink-soft uppercase transition-colors hover:bg-neon-pink/15 ${jp}`}
        >
          {t.landingFooterCta}
        </Link>
      </section>
    </main>
  );
}
