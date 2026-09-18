FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# These get inlined into the client bundle at build time, so they must be
# declared as ARG here — Render (and `docker build --build-arg`) only pass
# env vars into the build step for ARGs a Dockerfile explicitly declares.
# Changing them later needs a rebuild, not just a service restart.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SIGNALING_URL
ARG NEXT_PUBLIC_ADMIN_USERNAMES
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_SIGNALING_URL=$NEXT_PUBLIC_SIGNALING_URL
ENV NEXT_PUBLIC_ADMIN_USERNAMES=$NEXT_PUBLIC_ADMIN_USERNAMES

RUN npm run build

FROM node:20-slim

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

ENV PORT=3000
EXPOSE 3000

CMD npm start -- -p ${PORT}
