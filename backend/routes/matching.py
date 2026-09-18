from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from matching_queue import join_queue, get_current_room, leave_room

router = APIRouter(prefix="/matching", tags=["matching"])


class JoinRequest(BaseModel):
    tag: str | None = None  # e.g. "python", "react" — omit for random matching


class SkipRequest(BaseModel):
    tag: str | None = None  # requeue into the same tag they were matched under


def _user_id_from_token(current_user: dict) -> int:
    return int(current_user["sub"])


@router.post("/join")
def join(
    payload: JoinRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _user_id_from_token(current_user)
    result = join_queue(user_id, payload.tag, db)
    if result:
        return {"status": "matched", "room_id": result}
    return {"status": "waiting"}


@router.post("/skip")
def skip(
    payload: SkipRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Step 5.4 — leave the current room, then immediately requeue the user who
    skipped. The response's partner_id tells the caller (signaling server)
    who to notify so their call ends and they can requeue too.
    """
    user_id = _user_id_from_token(current_user)
    partner_id = leave_room(user_id, db)
    room_id = join_queue(user_id, payload.tag, db)

    return {
        "status": "matched" if room_id else "waiting",
        "room_id": room_id,
        "partner_id": partner_id,
    }


@router.get("/room/{user_id}")
def room_status(user_id: int, current_user: dict = Depends(get_current_user)):
    if int(current_user["sub"]) != user_id:
        return {"room_id": None}
    return {"room_id": get_current_room(user_id)}
