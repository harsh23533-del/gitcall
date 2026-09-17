import { useRouter } from "next/router";
import { useState } from "react";
import { useWebRTCCall } from "../../hooks/useWebRTCCall";

export default function CallRoom() {
  const router = useRouter();
  const roomId = typeof router.query.roomId === "string" ? router.query.roomId : undefined;

  const { status, localVideoRef, remoteVideoRef, chatLog, sendChatMessage, endCall } =
    useWebRTCCall(roomId);

  const [chatInput, setChatInput] = useState("");

  function handleSend() {
    if (!chatInput.trim()) return;
    sendChatMessage(chatInput.trim());
    setChatInput("");
  }

  function handleEndCall() {
    endCall();
    router.push("/dashboard");
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

        <div className="absolute top-4 left-4 text-sm text-gray-300 bg-black/50 px-3 py-1 rounded-full">
          {status === "connecting" && "Connecting…"}
          {status === "connected" && "Connected"}
          {status === "ended" && "Call ended — partner left"}
        </div>

        {/* Collapsible chat overlay — Phase 8, Step 8.1 */}
        <div className="absolute bottom-4 left-4 w-72 max-h-48 overflow-y-auto bg-black/60 rounded-lg p-3 space-y-1 text-sm">
          {chatLog.map((msg, i) => (
            <div key={i}>
              <span className="text-gray-400">{msg.from === "me" ? "You" : "Peer"}: </span>
              {msg.text}
            </div>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4 p-4 bg-gray-950">
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
          onClick={handleEndCall}
          className="px-6 py-2 rounded-md bg-red-600 hover:bg-red-500 font-medium"
        >
          End / Skip
        </button>
      </div>
    </main>
  );
}
