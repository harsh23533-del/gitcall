# DevConnect Frontend

Next.js + TypeScript app: GitHub login, dashboard, video call screen, chat overlay.

## Planned pages
- `/` — Landing page with "Sign in with GitHub"
- `/dashboard` — Profile summary, match mode selector, Start button
- `/call/[roomId]` — Video call screen (chat, code panel, report button)
- `/history` — Past matches and connections
- `/admin` — Moderation dashboard (protected)

## Setup
```bash
npm install
cp .env.local.example .env.local   # then fill in real values
npm run dev
```
