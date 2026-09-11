import type { Metadata } from "next";
import { JetBrains_Mono, Space_Grotesk, Spectral } from "next/font/google";
import "./globals.css";

// New design system's type pairing:
//  - Space Grotesk: structural/display -- nav, headings, UI chrome. A
//    geometric grotesk with a slightly technical character, echoing the
//    poster references' tracked-out display wordmarks (SUBSTANCE 04).
//  - Spectral: an elegant serif reserved for occasional evocative lines
//    -- the "beautiful" register, used sparingly against the mono/grotesk
//    technical noise, the way the references pair a delicate photographic
//    moment against HUD readouts.
//  - JetBrains Mono: every technical label, coordinate, index mark,
//    ornament -- the instrument-panel vocabulary (LV7, P0, 001.04).
const display = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

const serif = Spectral({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  style: ["normal", "italic"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Kagutsuchi",
  description: "Autonomous code security verification.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${serif.variable} ${mono.variable} h-full`}>
      <body className="min-h-full">{children}</body>
    </html>
  );
}
