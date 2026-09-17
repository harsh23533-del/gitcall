"""
Redis-backed matching queue.

Step 5.1 — Queue design: a waiting user's ID sits in a Redis list until a
second compatible user shows up; then both are popped and paired into a room.

Step 5.3 — Tag-based matching: each tag (tech stack / role / purpose) gets
its own queue key so users only match within the same tag. No tag = the
plain random queue.
"""

from redis_client import redis_client


def _queue_key(tag: str | None) -> str:
    return f"waiting_queue:{tag}" if tag else "waiting_queue"


def pair_users(user_a: str, user_b: str) -> str:
    room_id = f"room_{user_a}_{user_b}"
    redis_client.set(f"user:{user_a}:room", room_id)
    redis_client.set(f"user:{user_b}:room", room_id)
    redis_client.set(f"room:{room_id}:users", f"{user_a},{user_b}")
    return room_id


def join_queue(user_id: int, tag: str | None = None) -> str | None:
    """
    Step 5.2 / 5.3 — try to find a waiting partner in the (optionally tagged)
    queue. Returns the room_id if paired, or None if now waiting.
    """
    key = _queue_key(tag)
    uid = str(user_id)

    partner = redis_client.lpop(key)
    if partner and partner != uid:
        return pair_users(partner, uid)

    if partner == uid:
        # Same user already queued (double-click) — put it back, don't
        # pair with self.
        redis_client.rpush(key, partner)
        return None

    redis_client.rpush(key, uid)
    return None


def get_current_room(user_id: int) -> str | None:
    return redis_client.get(f"user:{user_id}:room")


def leave_room(user_id: int) -> str | None:
    """
    Step 5.4 — on skip/disconnect: clear the room mapping for both users and
    return the partner's ID so the signaling server can notify them to
    re-queue too.
    """
    uid = str(user_id)
    room_id = redis_client.get(f"user:{uid}:room")
    if not room_id:
        return None

    users_raw = redis_client.get(f"room:{room_id}:users")
    partner_id = None
    if users_raw:
        ids = users_raw.split(",")
        partner_id = next((u for u in ids if u != uid), None)
        for u in ids:
            redis_client.delete(f"user:{u}:room")

    redis_client.delete(f"room:{room_id}:users")
    return partner_id
