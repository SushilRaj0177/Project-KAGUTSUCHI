"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import ScrollProgress from "./components/ScrollProgress";
import { spawnRipple } from "./components/ripple";

const NAV_LINKS = [
  { href: "/", label: "Product" },
  { href: "/analyze", label: "Analyze" },
  { href: "/research", label: "Research" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <motion.header
      className="top"
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="wrap">
        <motion.span className="brand" whileHover={{ letterSpacing: "0.04em" }} transition={{ duration: 0.25 }}>
          WSQF-AI
        </motion.span>
        <nav className="nav-links">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link key={link.href} href={link.href} className={`nav-link${active ? " active" : ""}`}>
                {link.label}
                {active && <motion.span className="nav-underline" layoutId="nav-underline" transition={{ type: "spring", stiffness: 500, damping: 35 }} />}
              </Link>
            );
          })}
          <motion.a
            className="gh ripple-host"
            href="https://github.com/SushilRaj0177/Project-KAGUTSUCHI"
            onPointerDown={spawnRipple}
            whileHover={{ scale: 1.05, borderColor: "var(--accent)" }}
            whileTap={{ scale: 0.96 }}
            transition={{ duration: 0.2 }}
          >
            Source →
          </motion.a>
        </nav>
      </div>
      <ScrollProgress />
    </motion.header>
  );
}
