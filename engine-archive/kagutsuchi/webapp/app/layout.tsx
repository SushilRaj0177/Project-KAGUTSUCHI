import type { Metadata } from "next";
import { JetBrains_Mono, Noto_Sans_JP, Space_Grotesk } from "next/font/google";
import { SessionProvider } from "@/components/SessionProvider";
import { LanguageProvider } from "@/components/LanguageContext";
import "./globals.css";

const display = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

// Only loaded for the Japanese toggle (lib/i18n.ts) - Latin text keeps
// using `display`/`mono` above, this covers Japanese glyphs neither of
// those fonts includes.
const jp = Noto_Sans_JP({
  variable: "--font-jp",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

const SITE_URL = "https://project-kagutsuchi-ruddy.vercel.app";
const TITLE = "Kagutsuchi — Find it, exploit it, prove the fix";
const DESCRIPTION =
  "Kagutsuchi scans your code, then actually exploits what it finds in an isolated sandbox — nothing gets called a vulnerability on a guess, and nothing gets called fixed without a second exploit attempt failing.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: "Kagutsuchi",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable} ${jp.variable} h-full`}>
      <body className="min-h-full">
        <SessionProvider>
          <LanguageProvider>{children}</LanguageProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
