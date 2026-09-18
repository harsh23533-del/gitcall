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

### Auth model

The frontend's NextAuth session cookie stays fully managed by NextAuth (JWE-encrypted, as
usual). Separately, on login it signs a small HS256 API token (`session.apiToken`) containing
just `{ sub: <internal user id>, githubUsername }`, using the same secret as `JWT_SECRET` /
`NEXTAUTH_SECRET`. The browser sends that as `Authorization: Bearer <token>` on calls to the
FastAPI backend, which verifies it (`backend/auth.py`) and trusts its `sub` as the caller's
identity — request bodies no longer carry a self-reported `user_id`. The one exception is
`POST /users/sync`, called server-to-server by NextAuth's `jwt()` callback before an api token
exists yet; that's gated by a shared `INTERNAL_API_SECRET` header instead.

### Migrations

Schema changes go through Alembic (`backend/migrations/`), not the dev-only
`Base.metadata.create_all()` in `main.py`. Run `alembic upgrade head` from `backend/` after
setting `DATABASE_URL`.

## Running tests (Phase 11)

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Needs a Redis instance reachable at `REDIS_URL` (defaults to `redis://localhost:6379`) — the
matching-queue tests are integration tests against real Redis, not mocks. Postgres is not
required: tests point `DATABASE_URL` at a throwaway local SQLite file instead. The same suite
runs in CI on every push (`.github/workflows/ci.yml`), alongside a frontend typecheck + build
and a signaling-server syntax check.

## Deployment (Phase 12)

- **Frontend** → Vercel. Connect the repo, set the project root to `frontend/`, add the env vars
  from `frontend/.env.local.example` (with real values and your prod domain for `NEXTAUTH_URL`).
- **Backend + signaling server** → `render.yaml` at the repo root is a Render Blueprint that
  provisions both (via their Dockerfiles) plus managed Postgres and Redis in one go. Railway
  works too — point it at `backend/Dockerfile` / `signaling-server/Dockerfile` directly and wire
  up the same env vars by hand. Either way, set `JWT_SECRET`/`INTERNAL_API_SECRET` to match the
  frontend's `NEXTAUTH_SECRET`/`INTERNAL_API_SECRET` exactly.
- **coturn (TURN server)** → run on a small VPS (DigitalOcean droplet or similar) — managed
  platforms rarely host raw UDP relays well. Open UDP/TCP 3478 plus a relay port range, per
  coturn's own docs.
- **GitHub OAuth App** → once you have a real domain, add its callback URL
  (`https://<your-domain>/api/auth/callback/github`) to the OAuth App's settings.
- **Monitoring** → UptimeRobot (uptime) + Sentry (errors) on both frontend and backend, per the
  original build guide. Not wired up here — needs your own Sentry/UptimeRobot accounts.

## License

TBD
