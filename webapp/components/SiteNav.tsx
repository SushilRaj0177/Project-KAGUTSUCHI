"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthButton } from "@/components/AuthButton";

const LINKS = [
  { href: "/scan", label: "Scan" },
  { href: "/dashboard", label: "Live Runs" },
  { href: "/compare", label: "Compare" },
  { href: "/calibration", label: "Calibration" },
  { href: "/detector-proposals", label: "New Classes" },
];

export function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="mb-16 flex flex-wrap items-center justify-between gap-4">
      <Link href="/" className="text-sm font-semibold tracking-wide">
        KAGUTSUCHI
      </Link>
      <div className="flex flex-wrap items-center gap-5 text-sm">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={
              pathname === link.href
                ? "text-white"
                : "text-slate-400 transition-colors hover:text-white"
            }
          >
            {link.label}
          </Link>
        ))}
        <span className="h-4 w-px bg-slate-800" aria-hidden />
        <AuthButton />
      </div>
    </nav>
  );
}
