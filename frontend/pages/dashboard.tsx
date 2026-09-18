import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import LoginButton from "../components/LoginButton";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TAGS = [
  { value: "", label: "Random" },
  { value: "python", label: "Python" },
  { value: "react", label: "React" },
  { value: "mobile", label: "Mobile" },
];

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [tag, setTag] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/");
    }
  }, [status, router]);

  async function handleStart() {
    if (!session?.dbUserId || !session?.apiToken) {
      setError("Still setting up your profile — try again in a second.");
      return;
    }

    setSearching(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/matching/join`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.apiToken}`,
        },
        body: JSON.stringify({ tag: tag || null }),
      });
      const data = await res.json();

      if (data.status === "matched") {
        router.push(`/call/${data.room_id}?tag=${encodeURIComponent(tag || "")}`);
      } else {
        // Waiting for a partner — a real app would poll /matching/room/{id}
        // or listen on a socket event; kept simple here for the MVP.
        setError("Waiting for another developer to join… try Start again shortly.");
      }
    } catch {
      setError("Couldn't reach the matching service. Is the backend running?");
    } finally {
      setSearching(false);
    }
  }

  if (status === "loading" || !session) {
    return <main className="min-h-screen flex items-center justify-center">Loading…</main>;
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-4">
      <div className="flex items-center justify-between w-full max-w-md">
        <h1 className="text-2xl font-semibold">Welcome, {session.githubUsername}</h1>
        <div className="flex items-center gap-3">
          <a href="/history" className="text-sm text-gray-500 hover:text-gray-800">
            History
          </a>
          <LoginButton />
        </div>
      </div>

      <div className="w-full max-w-md border rounded-lg p-6 flex flex-col gap-4">
        <label className="text-sm text-gray-500">
          Match by
          <select
            value={tag}
            onChange={(e) => setTag(e.target.value)}
            className="mt-1 w-full border rounded-md px-3 py-2"
          >
            {TAGS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>

        <button
          onClick={handleStart}
          disabled={searching}
          className="w-full px-4 py-3 rounded-md bg-black text-white font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {searching ? "Finding a match…" : "Start"}
        </button>

        {error && <p className="text-sm text-amber-600">{error}</p>}
      </div>
    </main>
  );
}
