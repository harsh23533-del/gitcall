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
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    results = []
    for r in reports:
        reporter = db.query(User).filter(User.id == r.reporter_id).first()
        reported = db.query(User).filter(User.id == r.reported_id).first()
        results.append(
            {
                "id": r.id,
                "reporter_id": r.reporter_id,
                "reporter_username": reporter.username if reporter else None,
                "reported_id": r.reported_id,
                "reported_username": reported.username if reported else None,
                "reported_is_suspended": reported.is_suspended if reported else None,
                "reason": r.reason,
                "details": r.details,
                "status": r.status,
                "created_at": r.created_at,
            }
        )
    return results


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


class ResolveReportRequest(BaseModel):
    status: str  # "resolved" / "dismissed" / "pending"


@router.patch("/{report_id}")
def resolve_report(report_id: int, payload: ResolveReportRequest, db: Session = Depends(get_db)):
    """Admin dashboard action — mark a report reviewed."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"status": "not_found"}
    report.status = payload.status
    db.commit()
    return {"status": "updated", "report_id": report.id, "new_status": report.status}


@router.post("/{reported_id}/unsuspend")
def unsuspend_user(reported_id: int, db: Session = Depends(get_db)):
    """Admin dashboard action — lift an auto-suspension after review."""
    user = db.query(User).filter(User.id == reported_id).first()
    if not user:
        return {"status": "not_found"}
    user.is_suspended = False
    db.commit()
    return {"status": "unsuspended", "user_id": user.id}
