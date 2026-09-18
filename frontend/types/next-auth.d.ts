import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    githubId?: number;
    githubUsername?: string;
    avatarUrl?: string;
    dbUserId?: number;
    apiToken?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    githubId?: number;
    githubUsername?: string;
    avatarUrl?: string;
    dbUserId?: number;
    apiToken?: string;
  }
}
