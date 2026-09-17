from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Report, User, BlockedUser

router = APIRouter(prefix="/reports", tags=["reports"])

# Step 9.2 — auto-flag repeat offenders: if a user accumulates this many
# reports within the time window below, auto-suspend their account.
AUTO_SUSPEND_THRESHOLD = 3
AUTO_SUSPEND_WINDOW_HOURS = 24


class CreateReportRequest(BaseModel):
    reporter_id: int
    reported_id: int
    reason: str
    details: str | None = None
    evidence_url: str | None = None


@router.post("")
def create_report(payload: CreateReportRequest, db: Session = Depends(get_db)):
    report = Report(
        reporter_id=payload.reporter_id,
        reported_id=payload.reported_id,
        reason=payload.reason,
        details=payload.details,
        evidence_url=payload.evidence_url,
    )
    db.add(report)

    # Step 9.3 — block list: the reporter never gets matched with this user
    # again, regardless of what happens to the report.
    already_blocked = (
        db.query(BlockedUser)
        .filter(
            BlockedUser.blocker_id == payload.reporter_id,
            BlockedUser.blocked_id == payload.reported_id,
        )
        .first()
    )
    if not already_blocked:
        db.add(BlockedUser(blocker_id=payload.reporter_id, blocked_id=payload.reported_id))

    db.commit()
    db.refresh(report)

    # Step 9.2 — auto-flag: count recent reports against this user and
    # suspend if they cross the threshold.
    window_start = datetime.utcnow() - timedelta(hours=AUTO_SUSPEND_WINDOW_HOURS)
    recent_report_count = (
        db.query(Report)
        .filter(Report.reported_id == payload.reported_id, Report.created_at >= window_start)
        .count()
    )

    auto_suspended = False
    if recent_report_count >= AUTO_SUSPEND_THRESHOLD:
        user = db.query(User).filter(User.id == payload.reported_id).first()
        if user and not user.is_suspended:
            user.is_suspended = True
            db.commit()
            auto_suspended = True

    return {
        "status": "reported",
        "report_id": report.id,
        "recent_report_count": recent_report_count,
        "auto_suspended": auto_suspended,
    }


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    """Feeds the admin moderation dashboard (Phase 10, /admin)."""
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.post("/block")
def block_user(reporter_id: int, reported_id: int, db: Session = Depends(get_db)):
    """Manual block, independent of filing a report."""
    existing = (
        db.query(BlockedUser)
        .filter(BlockedUser.blocker_id == reporter_id, BlockedUser.blocked_id == reported_id)
        .first()
    )
    if not existing:
        db.add(BlockedUser(blocker_id=reporter_id, blocked_id=reported_id))
        db.commit()
    return {"status": "blocked"}
