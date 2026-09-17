import { signIn, signOut, useSession } from "next-auth/react";

export default function LoginButton() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <button className="px-4 py-2 rounded-md bg-gray-200 text-gray-500" disabled>
        Loading...
      </button>
    );
  }

  if (session) {
    return (
      <div className="flex items-center gap-3">
        {session.avatarUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={session.avatarUrl}
            alt={session.githubUsername ?? "avatar"}
            className="w-8 h-8 rounded-full"
          />
        )}
        <span className="text-sm font-medium">{session.githubUsername}</span>
        <button
          onClick={() => signOut()}
          className="px-4 py-2 rounded-md bg-gray-900 text-white hover:bg-gray-700"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => signIn("github")}
      className="px-4 py-2 rounded-md bg-black text-white hover:bg-gray-800"
    >
      Sign in with GitHub
    </button>
  );
}
