import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import LoginButton from "../components/LoginButton";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// MVP-only gate: comma-separated GitHub usernames allowed into /admin.
// Swap for real role-based access control before shipping past a demo.
const ADMIN_USERNAMES = (process.env.NEXT_PUBLIC_ADMIN_USERNAMES || "")
  .split(",")
  .map((u) => u.trim().toLowerCase())
  .filter(Boolean);

interface ReportRecord {
  id: number;
  reporter_id: number;
  reporter_username: string | null;
  reported_id: number;
  reported_username: string | null;
  reported_is_suspended: boolean | null;
  reason: string;
  details: string | null;
  status: string;
  created_at: string;
}

export default function Admin() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const isAdmin =
    !!session?.githubUsername &&
    (ADMIN_USERNAMES.length === 0 || ADMIN_USERNAMES.includes(session.githubUsername.toLowerCase()));

  useEffect(() => {
    if (status === "unauthenticated") router.push("/");
  }, [status, router]);

  useEffect(() => {
    if (!isAdmin || !session?.apiToken) return;
    fetch(`${API_URL}/reports`, {
      headers: { Authorization: `Bearer ${session.apiToken}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`status ${res.status}`);
        return res.json();
      })
      .then(setReports)
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, [isAdmin, session?.apiToken]);

  async function resolveReport(id: number, newStatus: string) {
    if (!session?.apiToken) return;
    await fetch(`${API_URL}/reports/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.apiToken}`,
      },
      body: JSON.stringify({ status: newStatus }),
    });
    setReports((rs) => rs.map((r) => (r.id === id ? { ...r, status: newStatus } : r)));
  }

  async function unsuspend(userId: number) {
    if (!session?.apiToken) return;
    await fetch(`${API_URL}/reports/${userId}/unsuspend`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session.apiToken}` },
    });
    setReports((rs) =>
      rs.map((r) => (r.reported_id === userId ? { ...r, reported_is_suspended: false } : r))
    );
  }

  if (status === "loading" || !session) {
    return <main className="min-h-screen flex items-center justify-center">Loading…</main>;
  }

  if (!isAdmin) {
    return (
      <main className="min-h-screen flex items-center justify-center text-gray-400">
        Not authorized.
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-10 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Moderation dashboard</h1>
        <LoginButton />
      </div>

      {loading && <p className="text-gray-400 text-sm">Loading…</p>}
      {!loading && reports.length === 0 && (
        <p className="text-gray-400 text-sm">No reports filed.</p>
      )}

      <div className="space-y-3">
        {reports.map((r) => (
          <div key={r.id} className="border rounded-lg p-4 text-sm space-y-2">
            <div className="flex justify-between">
              <div>
                <span className="font-medium">{r.reporter_username ?? `#${r.reporter_id}`}</span>
                <span className="text-gray-400"> reported </span>
                <span className="font-medium">{r.reported_username ?? `#${r.reported_id}`}</span>
              </div>
              <span className="text-gray-400">{new Date(r.created_at).toLocaleString()}</span>
            </div>

            <div className="text-gray-600">
              Reason: <span className="font-medium">{r.reason}</span>
              {r.details && <> — {r.details}</>}
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`px-2 py-0.5 rounded-full text-xs ${
                  r.status === "pending"
                    ? "bg-amber-100 text-amber-700"
                    : r.status === "resolved"
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                {r.status}
              </span>
              {r.reported_is_suspended && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-700">
                  suspended
                </span>
              )}

              <div className="ml-auto flex gap-2">
                {r.status === "pending" && (
                  <>
                    <button
                      onClick={() => resolveReport(r.id, "resolved")}
                      className="px-3 py-1 rounded-md bg-gray-800 text-white text-xs hover:bg-gray-700"
                    >
                      Resolve
                    </button>
                    <button
                      onClick={() => resolveReport(r.id, "dismissed")}
                      className="px-3 py-1 rounded-md bg-gray-100 text-xs hover:bg-gray-200"
                    >
                      Dismiss
                    </button>
                  </>
                )}
                {r.reported_is_suspended && (
                  <button
                    onClick={() => unsuspend(r.reported_id)}
                    className="px-3 py-1 rounded-md bg-gray-100 text-xs hover:bg-gray-200"
                  >
                    Unsuspend user
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
