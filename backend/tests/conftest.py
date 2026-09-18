import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Must be set before `main` (and therefore `database`) is imported, since the
# engine is created at import time from this env var.
os.environ["DATABASE_URL"] = "sqlite:///./test_ci.db"

import pytest
from fastapi.testclient import TestClient
from jose import jwt

import main
from database import Base, engine
from redis_client import redis_client

JWT_SECRET = os.getenv("JWT_SECRET", "generate_a_random_string")


@pytest.fixture()
def client():
    """
    A fresh set of tables + flushed Redis for every test — tests shouldn't
    see each other's queued users, matches, or reports. drop_all/create_all
    (rather than deleting the sqlite file on disk) avoids SQLAlchemy's
    connection pool holding a stale handle to an unlinked file. Requires a
    Redis instance reachable at REDIS_URL (see README's "Running tests"
    section).
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    redis_client.flushall()

    with TestClient(main.app) as c:
        yield c

    redis_client.flushall()


@pytest.fixture()
def make_token():
    """Signs the same shape of API token the frontend's NextAuth jwt() callback issues."""

    def _make(user_id: int, github_username: str = "tester") -> str:
        return jwt.encode(
            {"sub": str(user_id), "githubUsername": github_username},
            JWT_SECRET,
            algorithm="HS256",
        )

    return _make


@pytest.fixture()
def make_user(client):
    """Syncs a user via the real /users/sync endpoint and returns its internal id."""

    def _make(github_id: int, username: str) -> int:
        res = client.post(
            "/users/sync",
            json={"github_id": github_id, "username": username, "avatar_url": None, "bio": None},
        )
        assert res.status_code == 200, res.text
        return res.json()["user_id"]

    return _make
