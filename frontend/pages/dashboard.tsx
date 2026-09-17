import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
import { useEffect } from "react";
import LoginButton from "../components/LoginButton";

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/");
    }
  }, [status, router]);

  if (status === "loading" || !session) {
    return <main className="min-h-screen flex items-center justify-center">Loading…</main>;
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-4">
      <div className="flex items-center justify-between w-full max-w-md">
        <h1 className="text-2xl font-semibold">Welcome, {session.githubUsername}</h1>
        <LoginButton />
      </div>

      <div className="w-full max-w-md border rounded-lg p-6 text-center text-gray-400">
        Match mode selector + Start button land here once the Redis matching
        queue (Phase 5) and WebRTC call screen (Phase 6) are wired up.
      </div>
    </main>
  );
}
