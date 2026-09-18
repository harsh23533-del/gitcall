import os

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Match, User

router = APIRouter(prefix="/users", tags=["users"])

INTERNAL_API_SECRET = os.getenv("INTERNAL_API_SECRET")


class SyncUserRequest(BaseModel):
    github_id: int
    username: str
    avatar_url: str | None = None
    bio: str | None = None


@router.post("/sync")
def sync_user(
    payload: SyncUserRequest,
    db: Session = Depends(get_db),
    x_internal_secret: str | None = Header(default=None),
):
    """
    Upsert a user's GitHub-cached profile fields.
    Called server-to-server by the frontend's NextAuth jwt() callback on
    every successful login (before an api token exists yet, since this is
    what mints the internal user_id that goes *into* that token) — so it
    can't be gated by get_current_user like the rest of the API. Instead it
    checks a shared secret (INTERNAL_API_SECRET) that only the Next.js
    server, not a browser, would have.
    """
    if INTERNAL_API_SECRET and x_internal_secret != INTERNAL_API_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal secret")

    user = db.query(User).filter(User.github_id == payload.github_id).first()

    if user:
        user.username = payload.username
        user.avatar_url = payload.avatar_url
        user.bio = payload.bio
    else:
        user = User(
            github_id=payload.github_id,
            username=payload.username,
            avatar_url=payload.avatar_url,
            bio=payload.bio,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    return {"status": "synced", "user_id": user.id}


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Public-ish read of a user's cached GitHub profile fields — used for the
    in-call GitHub profile card (Phase 8, Step 8.4), so intentionally not
    gated behind get_current_user: both call participants need to look each
    other up, and nothing sensitive (access_token_enc) is returned here.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "top_languages": user.top_languages,
        "role": user.role,
        "looking_for": user.looking_for,
    }


@router.get("/{user_id}/matches")
def match_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Phase 10 — feeds the /history page."""
    if int(current_user["sub"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your match history")

    matches = (
        db.query(Match)
        .filter(or_(Match.user_a_id == user_id, Match.user_b_id == user_id))
        .order_by(Match.started_at.desc())
        .all()
    )

    results = []
    for m in matches:
        partner_id = m.user_b_id if m.user_a_id == user_id else m.user_a_id
        partner = db.query(User).filter(User.id == partner_id).first()
        results.append(
            {
                "match_id": m.id,
                "partner_id": partner_id,
                "partner_username": partner.username if partner else None,
                "match_mode": m.match_mode,
                "started_at": m.started_at,
                "ended_at": m.ended_at,
                "duration_seconds": m.duration_seconds,
            }
        )
    return results
