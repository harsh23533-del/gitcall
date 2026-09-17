// DevConnect signaling server: exchanges WebRTC SDP/ICE data between matched users.
// Full room-join / offer-answer / ice-candidate handlers land here once matching
// (Phase 5) and WebRTC setup (Phase 6) are wired up. See build guide, Phase 7.

require("dotenv").config();
const { Server } = require("socket.io");

const PORT = process.env.PORT || 4000;

const io = new Server(PORT, { cors: { origin: "*" } });

io.on("connection", (socket) => {
  console.log(`Client connected: ${socket.id}`);

  socket.on("disconnect", () => {
    console.log(`Client disconnected: ${socket.id}`);
  });
});

console.log(`Signaling server listening on port ${PORT}`);
