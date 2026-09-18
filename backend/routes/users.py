from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import User, Match

router = APIRouter(prefix="/users", tags=["users"])


class SyncUserRequest(BaseModel):
    github_id: int
    username: str
    avatar_url: str | None = None
    bio: str | None = None


@router.post("/sync")
def sync_user(payload: SyncUserRequest, db: Session = Depends(get_db)):
    """
    Upsert a user's GitHub-cached profile fields.
    Called by the frontend's NextAuth signIn event on every successful login,
    so the cached fields (avatar, bio, username) stay fresh.
    """
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
    return db.query(User).filter(User.id == user_id).first()


@router.get("/{user_id}/matches")
def get_user_matches(user_id: int, db: Session = Depends(get_db)):
    """Feeds the /history page — Phase 10, Step 10.1."""
    matches = (
        db.query(Match)
        .filter((Match.user_a_id == user_id) | (Match.user_b_id == user_id))
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
