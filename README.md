# DevConnect

Random video chat platform for verified engineers — GitHub-OAuth-gated video networking app.

## Core Idea
DevConnect only allows login through GitHub OAuth, so every user is a real, identity-linked developer.
This removes the anonymity/troll problem by design and enables smart matching by tech stack, role, or purpose.

## Architecture

| Component | Responsibility |
|---|---|
| `frontend/` (Next.js + TypeScript) | UI, GitHub login, video call screen, chat overlay |
| `backend/` (FastAPI) | User profiles, match history, reports, admin endpoints |
| `signaling-server/` (Socket.io) | Exchanges WebRTC SDP/ICE data between matched users |
| Redis | Live matching queue + pub/sub for signaling |
| PostgreSQL | Persistent data: users, matches, reports, chat logs |
| coturn (TURN/STUN) | Helps peers connect through NAT/firewalls |

Video/audio flows directly peer-to-peer between browsers (WebRTC) — it never touches the server.

## Local Development

1. Install prerequisites: Node.js 18+, Python 3.11+, Docker, Git.
2. Copy env templates and fill in real values:
   ```bash
   cp frontend/.env.local.example frontend/.env.local
   cp backend/.env.example backend/.env
   cp signaling-server/.env.example signaling-server/.env
   ```
3. Start Postgres, Redis, and coturn:
   ```bash
   docker-compose up -d
   ```
4. Run each service in its own terminal:
   ```bash
   # backend
   cd backend && python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000

   # frontend
   cd frontend && npm install && npm run dev

   # signaling server
   cd signaling-server && npm install && node index.js
   ```

## Project Structure

```
devconnect/
├── frontend/            # Next.js app
├── backend/             # FastAPI app
├── signaling-server/    # Socket.io server
├── docker-compose.yml   # Postgres + Redis + coturn
└── README.md
```

## Roadmap

See the full build guide for the phase-by-phase plan: OAuth, matching engine, WebRTC signaling,
in-call features, moderation, and deployment.

## License

TBD
