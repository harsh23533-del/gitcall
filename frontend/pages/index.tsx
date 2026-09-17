import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
import { useEffect } from "react";
import LoginButton from "../components/LoginButton";

export default function Home() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") {
      router.push("/dashboard");
    }
  }, [status, router]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-4 text-center">
      <h1 className="text-4xl font-bold">DevConnect</h1>
      <p className="text-gray-500 max-w-md">
        Random video chat for verified engineers. Sign in with GitHub to get
        matched with another real developer — no anonymous accounts, no bots.
      </p>
      <LoginButton />
      {session && <p className="text-sm text-gray-400">Redirecting to your dashboard…</p>}
    </main>
  );
}
