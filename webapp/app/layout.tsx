import type { Metadata } from "next";
import { Big_Shoulders, IBM_Plex_Mono, IBM_Plex_Sans, Noto_Sans_JP } from "next/font/google";
import { CursorFX } from "@/components/CursorFX";
import { LanguageProvider } from "@/components/LanguageContext";
import "./globals.css";

const display = Big_Shoulders({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["600", "800"],
});

const sans = IBM_Plex_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const mono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const jp = Noto_Sans_JP({
  variable: "--font-jp",
  subsets: ["latin"],
  weight: ["500", "700"],
});

export const metadata: Metadata = {
  title: "Kagutsuchi — 検証ダッシュボード",
  description: "Real verification runs: demonstrated exploits, proven fixes.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-theme="dark"
      className={`${display.variable} ${sans.variable} ${mono.variable} ${jp.variable} h-full`}
    >
      <body className="min-h-full">
        <CursorFX />
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
