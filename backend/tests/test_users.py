def test_sync_creates_user(client, make_user):
    user_id = make_user(github_id=1, username="alice")
    assert user_id is not None


def test_sync_upserts_existing_user(client):
    r1 = client.post("/users/sync", json={"github_id": 42, "username": "bob", "avatar_url": None, "bio": None})
    r2 = client.post(
        "/users/sync",
        json={"github_id": 42, "username": "bob-renamed", "avatar_url": "http://x/y.png", "bio": "hi"},
    )
    assert r1.json()["user_id"] == r2.json()["user_id"]

    profile = client.get(f"/users/{r2.json()['user_id']}").json()
    assert profile["username"] == "bob-renamed"
    assert profile["bio"] == "hi"


def test_get_unknown_user_404(client):
    res = client.get("/users/999999")
    assert res.status_code == 404


def test_match_history_requires_matching_token(client, make_user, make_token):
    uid = make_user(1, "alice")
    other_token = make_token(uid + 999)  # a token for someone else entirely

    res = client.get(f"/users/{uid}/matches", headers={"Authorization": f"Bearer {other_token}"})
    assert res.status_code == 403


def test_match_history_no_token_401(client, make_user):
    uid = make_user(1, "alice")
    res = client.get(f"/users/{uid}/matches")
    assert res.status_code == 401
