"""
Redis-backed matching queue.

Step 5.1 — Queue design: a waiting user's ID sits in a Redis list until a
second compatible user shows up; then both are popped and paired into a room.

Step 5.3 — Tag-based matching: each tag (tech stack / role / purpose) gets
its own queue key so users only match within the same tag. No tag = the
plain random queue.

Phase 9, Step 9.3 — join_queue optionally takes a `db` session so it can
skip candidates that are on each other's block list (see blocklist.py).
"""

from typing import Optional

from redis_client import redis_client

# Bound how many candidates we'll skip over looking for a non-blocked match,
# so one user with many blocks can't turn a join request into a long scan
# of the whole waiting queue.
MAX_BLOCK_SKIP_ATTEMPTS = 20


def _queue_key(tag: str | None) -> str:
    return f"waiting_queue:{tag}" if tag else "waiting_queue"


def pair_users(user_a: str, user_b: str, db: Optional[object] = None, match_mode: str | None = None) -> str:
    room_id = f"room_{user_a}_{user_b}"
    redis_client.set(f"user:{user_a}:room", room_id)
    redis_client.set(f"user:{user_b}:room", room_id)
    redis_client.set(f"room:{room_id}:users", f"{user_a},{user_b}")

    if db is not None:
        # Phase 10, Step 10.1 — record the match so /history has something
        # to show, and so leave_room() can fill in ended_at/duration later.
        from models import Match

        match = Match(user_a_id=int(user_a), user_b_id=int(user_b), match_mode=match_mode)
        db.add(match)
        db.commit()
        db.refresh(match)
        redis_client.set(f"room:{room_id}:match_id", str(match.id))

    return room_id


def join_queue(user_id: int, tag: str | None = None, db: Optional[object] = None) -> str | None:
    """
    Step 5.2 / 5.3 — try to find a waiting partner in the (optionally tagged)
    queue. Returns the room_id if paired, or None if now waiting.

    If `db` is passed, blocked pairs (Step 9.3) are skipped rather than
    matched — any skipped candidates are pushed back to the front of the
    queue in their original order so they aren't starved.
    """
    from blocklist import is_blocked_pair  # local import avoids a hard
    # dependency on the DB layer for callers that don't pass `db`.

    key = _queue_key(tag)
    uid = str(user_id)
    skipped: list[str] = []
    room_id: str | None = None

    for _ in range(MAX_BLOCK_SKIP_ATTEMPTS):
        partner = redis_client.lpop(key)
        if partner is None:
            break

        if partner == uid:
            # Same user already queued (double-click) — don't pair with self.
            skipped.append(partner)
            continue

        if db is not None and is_blocked_pair(db, int(partner), user_id):
            skipped.append(partner)
            continue

        room_id = pair_users(partner, uid, db=db, match_mode=tag or "random")
        break

    # Put back anything we skipped over, preserving their place in line.
    for candidate in reversed(skipped):
        redis_client.lpush(key, candidate)

    if room_id:
        return room_id

    redis_client.rpush(key, uid)
    return None


def get_current_room(user_id: int) -> str | None:
    return redis_client.get(f"user:{user_id}:room")


def leave_room(user_id: int, db: Optional[object] = None) -> str | None:
    """
    Step 5.4 — on skip/disconnect: clear the room mapping for both users and
    return the partner's ID so the signaling server can notify them to
    re-queue too.

    If `db` is passed, also closes out the Match row (Step 10.1) with
    ended_at/duration_seconds.
    """
    uid = str(user_id)
    room_id = redis_client.get(f"user:{uid}:room")
    if not room_id:
        return None

    if db is not None:
        match_id = redis_client.get(f"room:{room_id}:match_id")
        if match_id:
            from datetime import datetime, timezone
            from models import Match

            match = db.query(Match).filter(Match.id == int(match_id)).first()
            if match and not match.ended_at:
                now = datetime.now(timezone.utc)
                match.ended_at = now
                started = match.started_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                match.duration_seconds = int((now - started).total_seconds())
                db.commit()

    users_raw = redis_client.get(f"room:{room_id}:users")
    partner_id = None
    if users_raw:
        ids = users_raw.split(",")
        partner_id = next((u for u in ids if u != uid), None)
        for u in ids:
            redis_client.delete(f"user:{u}:room")

    redis_client.delete(f"room:{room_id}:users")
    redis_client.delete(f"room:{room_id}:match_id")
    return partner_id
