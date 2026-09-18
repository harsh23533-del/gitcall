import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import LoginButton from "../components/LoginButton";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MatchRecord {
  match_id: number;
  partner_id: number;
  partner_username: string | null;
  match_mode: string | null;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "in progress";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

export default function History() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/");
    }
  }, [status, router]);

  useEffect(() => {
    if (!session?.dbUserId || !session?.apiToken) return;
    fetch(`${API_URL}/users/${session.dbUserId}/matches`, {
      headers: { Authorization: `Bearer ${session.apiToken}` },
    })
      .then((res) => res.json())
      .then((data) => setMatches(data))
      .catch(() => setMatches([]))
      .finally(() => setLoading(false));
  }, [session?.dbUserId, session?.apiToken]);

  if (status === "loading" || !session) {
    return <main className="min-h-screen flex items-center justify-center">Loading…</main>;
  }

  return (
    <main className="min-h-screen flex flex-col items-center gap-6 px-4 py-10">
      <div className="flex items-center justify-between w-full max-w-lg">
        <h1 className="text-2xl font-semibold">Your match history</h1>
        <LoginButton />
      </div>

      <div className="w-full max-w-lg">
        {loading && <p className="text-gray-400 text-sm">Loading…</p>}

        {!loading && matches.length === 0 && (
          <p className="text-gray-400 text-sm">No matches yet — hit Start on your dashboard.</p>
        )}

        <ul className="space-y-2">
          {matches.map((m) => (
            <li key={m.match_id} className="border rounded-lg p-3 flex items-center justify-between text-sm">
              <div>
                <div className="font-medium">{m.partner_username ?? `User #${m.partner_id}`}</div>
                <div className="text-gray-400">
                  {m.match_mode || "random"} · {new Date(m.started_at).toLocaleString()}
                </div>
              </div>
              <div className="text-gray-500">{formatDuration(m.duration_seconds)}</div>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
