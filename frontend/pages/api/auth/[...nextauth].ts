import NextAuth, { type NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";

export const authOptions: NextAuthOptions = {
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_ID as string,
      clientSecret: process.env.GITHUB_SECRET as string,
      authorization: { params: { scope: "read:user user:email" } },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      // Runs on sign-in: attach the GitHub access token + username to the JWT.
      if (account && profile) {
        token.accessToken = account.access_token;
        token.githubId = (profile as { id?: number }).id;
        token.githubUsername = (profile as { login?: string }).login;
        token.avatarUrl = (profile as { avatar_url?: string }).avatar_url;
      }
      return token;
    },
    async session({ session, token }) {
      // Expose the fields the frontend needs without leaking the raw GitHub token
      // any further than necessary.
      session.githubId = token.githubId as number | undefined;
      session.githubUsername = token.githubUsername as string | undefined;
      session.avatarUrl = token.avatarUrl as string | undefined;
      return session;
    },
  },
  events: {
    // Step 2.6 — on every successful GitHub sign-in, upsert the user's
    // GitHub-cached profile fields into the backend (Postgres via FastAPI).
    async signIn({ profile }) {
      const apiUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl || !profile) return;

      const githubProfile = profile as {
        id?: number;
        login?: string;
        avatar_url?: string;
        bio?: string;
      };

      try {
        await fetch(`${apiUrl}/users/sync`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            github_id: githubProfile.id,
            username: githubProfile.login,
            avatar_url: githubProfile.avatar_url,
            bio: githubProfile.bio ?? null,
          }),
        });
      } catch (err) {
        // Don't block sign-in if the backend sync call fails — log and move on.
        console.error("users/sync failed:", err);
      }
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};

export default NextAuth(authOptions);
