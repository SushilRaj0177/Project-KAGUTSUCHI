import type { Metadata } from "next";
import "./globals.css";

// Front-end stripped down to a bare shell on purpose (see COORDINATION.md /
// the conversation that led here) - fonts, providers, and every visual
// primitive were deliberately removed rather than restyled in place, so
// the rebuild starts from nothing instead of quietly inheriting the old
// layout's structure. Nothing here should be treated as "the base" to
// build on top of - replace this whole file once the new design's fonts
// and providers are known.

export const metadata: Metadata = {
  title: "Kagutsuchi",
  description: "Autonomous code security verification.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
