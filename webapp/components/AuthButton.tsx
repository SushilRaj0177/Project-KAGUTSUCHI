"use client";

import { signIn, signOut, useSession } from "next-auth/react";

export function AuthButton() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <span className="text-xs text-slate-600">…</span>;
  }

  if (session?.user) {
    return (
      <button
        onClick={() => signOut()}
        className="text-xs text-slate-400 transition-colors hover:text-white"
        title={`Signed in as ${session.user.name ?? session.user.email ?? "GitHub user"}`}
      >
        Sign out
      </button>
    );
  }

  return (
    <button onClick={() => signIn("github")} className="text-xs text-slate-400 transition-colors hover:text-white">
      Sign in with GitHub
    </button>
  );
}
