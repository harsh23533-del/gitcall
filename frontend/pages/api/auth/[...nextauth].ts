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
      // Runs on sign-in: attach the GitHub access token + username to the JWT,
      // and sync the profile to the backend so we get back our internal
      // integer user_id (needed for /matching/join, /matching/skip, etc. —
      // the backend's DB id, not GitHub's numeric id).
      if (account && profile) {
        token.accessToken = account.access_token;
        token.githubId = (profile as { id?: number }).id;
        token.githubUsername = (profile as { login?: string }).login;
        token.avatarUrl = (profile as { avatar_url?: string }).avatar_url;

        const apiUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL;
        const githubProfile = profile as {
          id?: number;
          login?: string;
          avatar_url?: string;
          bio?: string;
        };

        if (apiUrl) {
          try {
            const res = await fetch(`${apiUrl}/users/sync`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                github_id: githubProfile.id,
                username: githubProfile.login,
                avatar_url: githubProfile.avatar_url,
                bio: githubProfile.bio ?? null,
              }),
            });
            const data = await res.json();
            token.dbUserId = data.user_id;
          } catch (err) {
            // Don't block sign-in if the backend sync call fails — log and
            // move on; dbUserId just won't be set this session.
            console.error("users/sync failed:", err);
          }
        }
      }
      return token;
    },
    async session({ session, token }) {
      // Expose the fields the frontend needs without leaking the raw GitHub token
      // any further than necessary.
      session.githubId = token.githubId as number | undefined;
      session.githubUsername = token.githubUsername as string | undefined;
      session.avatarUrl = token.avatarUrl as string | undefined;
      session.dbUserId = token.dbUserId as number | undefined;
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};

export default NextAuth(authOptions);
