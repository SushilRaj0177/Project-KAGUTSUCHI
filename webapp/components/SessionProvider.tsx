"use client";

import { SessionProvider as NextAuthSessionProvider } from "next-auth/react";

// Thin client wrapper so layout.tsx (a server component) can still use
// next-auth's client hooks (useSession) anywhere below it in the tree.
export function SessionProvider({ children }: { children: React.ReactNode }) {
  return <NextAuthSessionProvider>{children}</NextAuthSessionProvider>;
}
