from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from matching_queue import join_queue, get_current_room, leave_room

router = APIRouter(prefix="/matching", tags=["matching"])


class JoinRequest(BaseModel):
    user_id: int
    tag: str | None = None  # e.g. "python", "react" — omit for random matching


class SkipRequest(BaseModel):
    user_id: int
    tag: str | None = None  # requeue into the same tag they were matched under


@router.post("/join")
def join(payload: JoinRequest, db: Session = Depends(get_db)):
    room_id = join_queue(payload.user_id, payload.tag, db=db)
    if room_id:
        return {"status": "matched", "room_id": room_id}
    return {"status": "waiting"}


@router.post("/skip")
def skip(payload: SkipRequest, db: Session = Depends(get_db)):
    """
    Step 5.4 — leave the current room, then immediately requeue the user who
    skipped. The response's partner_id tells the caller (signaling server)
    who to notify so their call ends and they can requeue too.
    """
    partner_id = leave_room(payload.user_id, db=db)
    room_id = join_queue(payload.user_id, payload.tag, db=db)

    return {
        "status": "matched" if room_id else "waiting",
        "room_id": room_id,
        "partner_id": partner_id,
    }


@router.get("/room/{user_id}")
def room_status(user_id: int):
    return {"room_id": get_current_room(user_id)}
