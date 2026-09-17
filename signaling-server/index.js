// DevConnect signaling server: exchanges WebRTC SDP/ICE data between matched
// users. See build guide, Phase 7. Relays offer/answer/ice-candidate between
// the two sockets in a room; actual video/audio never passes through here.

require("dotenv").config();
const { Server } = require("socket.io");
const { filterProfanity } = require("./profanityFilter");

const PORT = process.env.PORT || 4000;

const io = new Server(PORT, { cors: { origin: "*" } });

// roomId -> Set of socket.ids currently in that room (used to notify the
// remaining peer when someone disconnects, since we don't get their userId
// on a raw socket disconnect).
const roomMembers = new Map();

function addToRoom(roomId, socketId) {
  if (!roomMembers.has(roomId)) roomMembers.set(roomId, new Set());
  roomMembers.get(roomId).add(socketId);
}

function removeFromRoom(roomId, socketId) {
  const members = roomMembers.get(roomId);
  if (!members) return;
  members.delete(socketId);
  if (members.size === 0) roomMembers.delete(roomId);
}

io.on("connection", (socket) => {
  console.log(`Client connected: ${socket.id}`);

  // Step 7.2 — a user enters the room matched for them by the backend
  // (Phase 5's room_id). Both peers must join before offer/answer starts.
  socket.on("join-room", (roomId) => {
    socket.join(roomId);
    socket.data.roomId = roomId;
    addToRoom(roomId, socket.id);

    // Tell whoever's already in the room that a peer has joined, so the
    // first one in knows it's safe to create the WebRTC offer.
    socket.to(roomId).emit("peer-joined", { socketId: socket.id });
  });

  socket.on("webrtc-offer", ({ roomId, offer }) => {
    socket.to(roomId).emit("webrtc-offer", { offer, from: socket.id });
  });

  socket.on("webrtc-answer", ({ roomId, answer }) => {
    socket.to(roomId).emit("webrtc-answer", { answer, from: socket.id });
  });

  socket.on("ice-candidate", ({ roomId, candidate }) => {
    socket.to(roomId).emit("ice-candidate", { candidate, from: socket.id });
  });

  // Step 8.1 — text chat overlay, relayed the same way as signaling messages.
  // Step 9.4 — run through a basic profanity filter before relaying.
  socket.on("chat-message", ({ roomId, text }) => {
    socket.to(roomId).emit("chat-message", { text: filterProfanity(text), from: socket.id });
  });

  // Step 8.2 — shared code snippet panel, relayed to the other peer in the room.
  socket.on("code-update", ({ roomId, content }) => {
    socket.to(roomId).emit("code-update", { content, from: socket.id });
  });

  socket.on("leave-room", ({ roomId }) => {
    socket.to(roomId).emit("peer-left", { socketId: socket.id });
    socket.leave(roomId);
    removeFromRoom(roomId, socket.id);
  });

  socket.on("disconnect", () => {
    console.log(`Client disconnected: ${socket.id}`);
    const roomId = socket.data.roomId;
    if (roomId) {
      // Notify the remaining peer so their UI can end the call and
      // trigger a re-queue via POST /matching/skip on the backend.
      socket.to(roomId).emit("peer-left", { socketId: socket.id });
      removeFromRoom(roomId, socket.id);
    }
  });
});

console.log(`Signaling server listening on port ${PORT}`);
