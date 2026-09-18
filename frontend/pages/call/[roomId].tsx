import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useWebRTCCall } from "../../hooks/useWebRTCCall";
import ReportModal from "../../components/ReportModal";
import PartnerProfileCard from "../../components/PartnerProfileCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** room_id is "room_{userA}_{userB}" (see backend/matching_queue.py) — pull
 *  the *other* user's id out of it so the report button / profile card /
 *  skip flow know who the partner is. */
function getPartnerId(roomId: string | undefined, myId: number | undefined): number | null {
  if (!roomId || !myId) return null;
  const parts = roomId.replace(/^room_/, "").split("_");
  const other = parts.find((p) => Number(p) !== myId);
  return other ? Number(other) : null;
}

export default function CallRoom() {
  const router = useRouter();
  const { data: session } = useSession();
  const roomId = typeof router.query.roomId === "string" ? router.query.roomId : undefined;
  const tag = typeof router.query.tag === "string" ? router.query.tag : "";

  const {
    status,
    localVideoRef,
    remoteVideoRef,
    chatLog,
    sendChatMessage,
    endCall,
    isScreenSharing,
    toggleScreenShare,
    codeContent,
    updateCode,
  } = useWebRTCCall(roomId);

  const [chatInput, setChatInput] = useState("");
  const [showCodePanel, setShowCodePanel] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reportSent, setReportSent] = useState(false);
  const [skipping, setSkipping] = useState(false);

  const partnerId = getPartnerId(roomId, session?.dbUserId);

  function handleSend() {
    if (!chatInput.trim()) return;
    sendChatMessage(chatInput.trim());
    setChatInput("");
  }

  // Step 5.4 — actually tell the backend the call ended: this closes out the
  // Postgres match row (see backend/matching_queue.leave_room) and
  // immediately tries to find the person a new match under the same tag
  // they started with. /matching/skip requires a bearer token now (see
  // backend/routes/matching.py), so this can't just fire-and-forget with a
  // plain user_id body anymore.
  async function handleEndCall() {
    endCall();

    if (!session?.apiToken) {
      router.push("/dashboard");
      return;
    }

    setSkipping(true);
    try {
      const res = await fetch(`${API_URL}/matching/skip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.apiToken}`,
        },
        body: JSON.stringify({ tag: tag || null }),
      });
      const data = await res.json();
      if (data.status === "matched" && data.room_id) {
        router.push(`/call/${data.room_id}?tag=${encodeURIComponent(tag)}`);
        return;
      }
    } catch (err) {
      console.error("Failed to notify backend of call end", err);
    } finally {
      setSkipping(false);
    }

    router.push("/dashboard");
  }

  async function handleReportSubmit(reason: string, details: string) {
    if (!session?.dbUserId || !partnerId || !session?.apiToken) {
      setShowReport(false);
      return;
    }

    try {
      await fetch(`${API_URL}/reports`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.apiToken}`,
        },
        body: JSON.stringify({
          reporter_id: session.dbUserId,
          reported_id: partnerId,
          reason,
          details: details || null,
        }),
      });
      setReportSent(true);
    } catch (err) {
      console.error("Failed to submit report", err);
    } finally {
      setShowReport(false);
    }
  }

  return (
    <main className="min-h-screen bg-black text-white flex flex-col">
      <div className="flex-1 relative flex items-center justify-center">
        {/* Remote video fills the screen */}
        <video
          ref={remoteVideoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover bg-gray-900"
        />

        {/* Local video, small corner tile */}
        <video
          ref={localVideoRef}
          autoPlay
          playsInline
          muted
          className="absolute bottom-4 right-4 w-40 h-28 rounded-lg border border-gray-700 object-cover bg-gray-800"
        />

        <div className="absolute top-4 left-4 flex items-center gap-2">
          <PartnerProfileCard userId={partnerId} />
          <span className="text-sm text-gray-300 bg-black/50 px-3 py-1 rounded-full">
            {status === "connecting" && "Connecting…"}
            {status === "connected" && "Connected"}
            {status === "ended" && "Call ended — partner left"}
          </span>
          {isScreenSharing && (
            <span className="text-sm text-amber-300 bg-black/50 px-3 py-1 rounded-full">
              Sharing screen
            </span>
          )}
        </div>

        {/* Report button — Phase 9, Step 9.1: always visible during calls */}
        <button
          onClick={() => setShowReport(true)}
          className="absolute top-4 right-4 text-sm bg-black/50 hover:bg-black/70 px-3 py-1 rounded-full"
        >
          Report
        </button>

        {/* Collapsible chat overlay — Phase 8, Step 8.1 */}
        <div className="absolute bottom-4 left-4 w-72 max-h-48 overflow-y-auto bg-black/60 rounded-lg p-3 space-y-1 text-sm">
          {chatLog.map((msg, i) => (
            <div key={i}>
              <span className="text-gray-400">{msg.from === "me" ? "You" : "Peer"}: </span>
              {msg.text}
            </div>
          ))}
        </div>

        {/* Code snippet panel — Phase 8, Step 8.2 */}
        {showCodePanel && (
          <textarea
            value={codeContent}
            onChange={(e) => updateCode(e.target.value)}
            placeholder="// Shared code — both of you can type here"
            className="absolute top-16 right-4 w-80 h-56 bg-gray-900 text-green-300 font-mono text-xs p-3 rounded-lg border border-gray-700 resize-none focus:outline-none"
          />
        )}

        {reportSent && (
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 bg-green-600 text-white text-sm px-4 py-2 rounded-full">
            Report submitted
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-3 p-4 bg-gray-950 flex-wrap">
        <input
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Say something…"
          className="flex-1 max-w-sm px-3 py-2 rounded-md bg-gray-800 text-sm focus:outline-none"
        />
        <button
          onClick={handleSend}
          className="px-4 py-2 rounded-md bg-gray-700 hover:bg-gray-600 text-sm"
        >
          Send
        </button>
        <button
          onClick={() => setShowCodePanel((v) => !v)}
          className="px-4 py-2 rounded-md bg-gray-700 hover:bg-gray-600 text-sm"
        >
          {showCodePanel ? "Hide code" : "Code panel"}
        </button>
        <button
          onClick={toggleScreenShare}
          className="px-4 py-2 rounded-md bg-gray-700 hover:bg-gray-600 text-sm"
        >
          {isScreenSharing ? "Stop sharing" : "Share screen"}
        </button>
        <button
          onClick={handleEndCall}
          disabled={skipping}
          className="px-6 py-2 rounded-md bg-red-600 hover:bg-red-500 font-medium disabled:opacity-50"
        >
          {skipping ? "Finding next…" : "End / Skip"}
        </button>
      </div>

      {showReport && (
        <ReportModal onSubmit={handleReportSubmit} onClose={() => setShowReport(false)} />
      )}
    </main>
  );
}
