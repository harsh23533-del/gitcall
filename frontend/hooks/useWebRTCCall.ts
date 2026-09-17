import { useEffect, useRef, useState } from "react";
import { io, type Socket } from "socket.io-client";

const SIGNALING_URL =
  process.env.NEXT_PUBLIC_SIGNALING_URL || "http://localhost:4000";

const ICE_SERVERS: RTCIceServer[] = [
  { urls: "stun:stun.l.google.com:19302" },
  // TURN (coturn) is added here once deployed — Phase 12, Step 12.3.
  // { urls: "turn:your-coturn-server:3478", username: "user", credential: "pass" },
];

export type CallStatus = "idle" | "connecting" | "connected" | "ended";

/**
 * Drives one WebRTC call inside a given signaling room:
 * - Step 6.1: local camera/mic
 * - Step 6.2-6.4: RTCPeerConnection + offer/answer/ICE exchange
 * - Phase 7 (client side): socket.io signaling transport
 */
export function useWebRTCCall(roomId: string | undefined) {
  const [status, setStatus] = useState<CallStatus>("idle");
  const [chatLog, setChatLog] = useState<{ from: string; text: string }[]>([]);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [codeContent, setCodeContent] = useState("");

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const cameraTrackRef = useRef<MediaStreamTrack | null>(null);

  useEffect(() => {
    if (!roomId) return;
    let cancelled = false;

    async function start() {
      setStatus("connecting");

      // Step 6.1 — local camera/mic
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      if (cancelled) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      localStreamRef.current = stream;
      cameraTrackRef.current = stream.getVideoTracks()[0] ?? null;
      if (localVideoRef.current) localVideoRef.current.srcObject = stream;

      // Step 6.2 — peer connection
      const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
      pcRef.current = pc;
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      pc.ontrack = (event) => {
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = event.streams[0];
        }
        setStatus("connected");
      };

      // Phase 7 client side — connect to the signaling server and join the room
      const socket = io(SIGNALING_URL);
      socketRef.current = socket;

      socket.on("connect", () => {
        socket.emit("join-room", roomId);
      });

      // Step 6.3 — whoever is already in the room creates the offer once a
      // second peer joins.
      socket.on("peer-joined", async () => {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        socket.emit("webrtc-offer", { roomId, offer });
      });

      socket.on("webrtc-offer", async ({ offer }: { offer: RTCSessionDescriptionInit }) => {
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        socket.emit("webrtc-answer", { roomId, answer });
      });

      // Step 6.4 — handle answer + ICE candidates
      socket.on("webrtc-answer", async ({ answer }: { answer: RTCSessionDescriptionInit }) => {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
      });

      pc.onicecandidate = (event) => {
        if (event.candidate) {
          socket.emit("ice-candidate", { roomId, candidate: event.candidate });
        }
      };

      socket.on("ice-candidate", async ({ candidate }: { candidate: RTCIceCandidateInit }) => {
        try {
          await pc.addIceCandidate(new RTCIceCandidate(candidate));
        } catch (err) {
          console.error("Failed to add ICE candidate", err);
        }
      });

      // Step 8.1 — chat overlay
      socket.on("chat-message", ({ from, text }: { from: string; text: string }) => {
        setChatLog((log) => [...log, { from, text }]);
      });

      // Step 8.2 — shared code snippet panel: relay content changes to the peer.
      socket.on("code-update", ({ content }: { content: string }) => {
        setCodeContent(content);
      });

      socket.on("peer-left", () => {
        setStatus("ended");
      });
    }

    start();

    return () => {
      cancelled = true;
      socketRef.current?.emit("leave-room", { roomId });
      socketRef.current?.disconnect();
      pcRef.current?.close();
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, [roomId]);

  function sendChatMessage(text: string) {
    if (!roomId) return;
    socketRef.current?.emit("chat-message", { roomId, text });
    setChatLog((log) => [...log, { from: "me", text }]);
  }

  // Step 8.2 — code snippet panel: broadcast local edits to the peer.
  function updateCode(content: string) {
    setCodeContent(content);
    if (!roomId) return;
    socketRef.current?.emit("code-update", { roomId, content });
  }

  // Step 8.3 — screen share: swap the outgoing video track for a display
  // track, and swap it back when the person stops sharing.
  async function toggleScreenShare() {
    const pc = pcRef.current;
    if (!pc) return;

    const sender = pc.getSenders().find((s) => s.track?.kind === "video");
    if (!sender) return;

    if (!isScreenSharing) {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        const screenTrack = screenStream.getVideoTracks()[0];
        await sender.replaceTrack(screenTrack);

        if (localVideoRef.current) localVideoRef.current.srcObject = screenStream;
        setIsScreenSharing(true);

        // If the user stops sharing via the browser's own "Stop sharing"
        // control, fall back to the camera automatically.
        screenTrack.onended = () => {
          void stopScreenShareInternal();
        };
      } catch (err) {
        console.error("Screen share failed or was cancelled", err);
      }
    } else {
      await stopScreenShareInternal();
    }

    async function stopScreenShareInternal() {
      const cameraTrack = cameraTrackRef.current;
      if (cameraTrack) {
        await sender!.replaceTrack(cameraTrack);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = localStreamRef.current;
        }
      }
      setIsScreenSharing(false);
    }
  }

  function endCall() {
    socketRef.current?.emit("leave-room", { roomId });
    setStatus("ended");
  }

  return {
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
  };
}
