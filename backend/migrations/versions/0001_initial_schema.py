"""initial schema — users, matches, connections, reports, blocked_users

Revision ID: 0001
Revises:
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("github_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("top_languages", sa.JSON(), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("looking_for", sa.String(length=50), nullable=True),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("is_suspended", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index("ix_users_github_id", "users", ["github_id"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_a_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("user_b_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("match_mode", sa.String(length=30), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
    )

    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("friend_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("connected_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reported_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reason", sa.String(length=100), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("evidence_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="pending"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    op.create_table(
        "blocked_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("blocker_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("blocked_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("blocked_users")
    op.drop_table("reports")
    op.drop_table("connections")
    op.drop_table("matches")
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_table("users")
