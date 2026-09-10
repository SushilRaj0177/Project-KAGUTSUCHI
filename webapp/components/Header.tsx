"use client";

import { useState } from "react";
import Link from "next/link";
import { BackendStatus } from "./BackendStatus";
import { useLanguage } from "./LanguageContext";
import { LanguageToggle } from "./LanguageToggle";

export function Header() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = [
    { href: "/", label: t.navHome },
    { href: "/scan", label: t.navScan },
    { href: "/dashboard", label: t.navDashboard },
    { href: "/compare", label: t.navCompare },
    { href: "/calibration", label: t.navCalibration },
    { href: "/detector-proposals", label: t.navDetectorProposals },
  ];

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
          <button
            type="button"
            data-cursor="hover"
            onClick={() => setMobileOpen((open) => !open)}
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation menu"
            className="border border-line-strong px-2.5 py-1.5 font-mono text-xs uppercase tracking-wide text-steel-400 transition-colors hover:border-neon-cyan hover:text-neon-cyan sm:hidden"
          >
            {mobileOpen ? "✕" : "☰"}
          </button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-neon-cyan cursor-blink" />
          <p className={`text-xs tracking-wide text-steel-400 uppercase ${jp}`}>{t.tagline}</p>
        </div>

        {/* Desktop nav — unchanged from before, just hidden below `sm` in
            favor of the hamburger-triggered menu below (was wrapping into
            two extra cramped lines on a phone-width screen). */}
        <nav className={`hidden flex-wrap items-center gap-x-5 gap-y-1 text-xs tracking-wide text-steel-400 uppercase sm:flex ${jp}`}>
          {navLinks.map((link) => (
            <Link
              key={link.href}
              data-cursor="hover"
              href={link.href}
              className="whitespace-nowrap transition-colors hover:text-neon-cyan"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>

      {mobileOpen && (
        <nav
          className={`fade-in-up mt-4 flex flex-col gap-4 border-t border-line pt-4 text-xs tracking-wide text-steel-400 uppercase sm:hidden ${jp}`}
        >
          {navLinks.map((link) => (
            <Link
              key={link.href}
              data-cursor="hover"
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className="transition-colors hover:text-neon-cyan"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
