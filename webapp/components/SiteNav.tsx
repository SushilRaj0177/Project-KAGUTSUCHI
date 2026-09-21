"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthButton } from "@/components/AuthButton";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useLanguage } from "@/components/LanguageContext";

export function SiteNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";

  const links = [
    { href: "/scan", label: t.navScan },
    { href: "/dashboard", label: t.navDashboard },
    { href: "/compare", label: t.navCompare },
    { href: "/calibration", label: t.navCalibration },
    { href: "/detector-proposals", label: t.navDetectorProposals },
  ];

  return (
    <nav className="mb-16">
      <div className="flex items-center justify-between gap-4">
        <Link href="/" className="text-sm font-semibold tracking-wide">
          KAGUTSUCHI
        </Link>

        {/* Desktop: full link list inline. */}
        <div className={`hidden items-center gap-5 text-sm sm:flex ${jp}`}>
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? "text-white" : "text-slate-400 transition-colors hover:text-white"}
            >
              {link.label}
            </Link>
          ))}
          <span className="h-4 w-px bg-slate-800" aria-hidden />
          <LanguageToggle />
          <AuthButton />
        </div>

        {/* Mobile: a single hamburger toggle instead of wrapping links. */}
        <button
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
          aria-expanded={open}
          className="flex h-8 w-8 flex-col items-center justify-center gap-1.5 sm:hidden"
        >
          <span className={`h-px w-5 bg-slate-300 transition-transform ${open ? "translate-y-[3.5px] rotate-45" : ""}`} />
          <span className={`h-px w-5 bg-slate-300 transition-transform ${open ? "-translate-y-[3.5px] -rotate-45" : ""}`} />
        </button>
      </div>

      {open && (
        <div className={`mt-4 flex flex-col gap-3 border-t border-slate-800 pt-4 text-sm sm:hidden ${jp}`}>
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className={pathname === link.href ? "text-white" : "text-slate-400"}
            >
              {link.label}
            </Link>
          ))}
          <div className="flex items-center justify-between border-t border-slate-800 pt-3">
            <AuthButton />
            <LanguageToggle />
          </div>
        </div>
      )}
    </nav>
  );
}
