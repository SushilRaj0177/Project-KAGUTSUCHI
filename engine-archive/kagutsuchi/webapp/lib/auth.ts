import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

// Replaces the PAT-paste MVP: signing in here gets a real GitHub OAuth
// access token with `repo` scope, stored server-side in the session JWT
// (never sent to client JS - see app/api/backend/open-pr/route.ts, which
// reads it via `auth()` instead of trusting a client-supplied token).
// Falls back to the old paste-a-PAT flow for anyone who'd rather not
// sign in - see FindingCard.tsx.
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
      authorization: { params: { scope: "read:user repo" } },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, account }) {
      // `account` is only present on the initial sign-in request, not on
      // every subsequent session read - this is the one place the OAuth
      // access token is ever available, so it has to be copied onto the
      // long-lived JWT here.
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      if (typeof token.accessToken === "string") {
        session.accessToken = token.accessToken;
      }
      return session;
    },
  },
});
