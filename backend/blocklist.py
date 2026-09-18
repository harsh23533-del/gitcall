from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models import BlockedUser


def is_blocked_pair(db: Session, user_a: int, user_b: int) -> bool:
    """True if either user has blocked the other (block is one-directional
    in storage but treated as mutual for matching purposes)."""
    return (
        db.query(BlockedUser)
        .filter(
            or_(
                and_(BlockedUser.blocker_id == user_a, BlockedUser.blocked_id == user_b),
                and_(BlockedUser.blocker_id == user_b, BlockedUser.blocked_id == user_a),
            )
        )
        .first()
        is not None
    )
