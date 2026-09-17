from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    JSON,
    TIMESTAMP,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    top_languages = Column(JSON, nullable=True)  # e.g. ["Python", "TypeScript"]
    role = Column(String(50), nullable=True)  # student / SDE / freelancer
    looking_for = Column(String(50), nullable=True)  # job / collab / mentorship / chat
    access_token_enc = Column(Text, nullable=True)  # encrypted GitHub token
    created_at = Column(TIMESTAMP, server_default=func.now())


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id"))
    user_b_id = Column(Integer, ForeignKey("users.id"))
    match_mode = Column(String(30), nullable=True)  # random / tech_stack / role / purpose
    started_at = Column(TIMESTAMP, server_default=func.now())
    ended_at = Column(TIMESTAMP, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))
    connected_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    reported_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    evidence_url = Column(Text, nullable=True)
    status = Column(String(30), default="pending")
    created_at = Column(TIMESTAMP, server_default=func.now())

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported = relationship("User", foreign_keys=[reported_id])
