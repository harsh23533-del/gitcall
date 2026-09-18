def test_two_users_get_matched(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta, tb = make_token(a), make_token(b)

    r1 = client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    assert r1.json()["status"] == "waiting"

    r2 = client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {tb}"})
    assert r2.json()["status"] == "matched"
    assert r2.json()["room_id"] == f"room_{a}_{b}"


def test_tag_based_matching_is_isolated(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta, tb = make_token(a), make_token(b)

    client.post("/matching/join", json={"tag": "python"}, headers={"Authorization": f"Bearer {ta}"})
    # different tag — should NOT match with `a`
    r = client.post("/matching/join", json={"tag": "react"}, headers={"Authorization": f"Bearer {tb}"})
    assert r.json()["status"] == "waiting"


def test_join_requires_auth(client):
    res = client.post("/matching/join", json={"tag": None})
    assert res.status_code in (401, 403)


def test_match_creates_history_row_for_both_users(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta, tb = make_token(a), make_token(b)

    client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {tb}"})

    history_a = client.get(f"/users/{a}/matches", headers={"Authorization": f"Bearer {ta}"}).json()
    history_b = client.get(f"/users/{b}/matches", headers={"Authorization": f"Bearer {tb}"}).json()

    assert len(history_a) == 1 and history_a[0]["partner_id"] == b
    assert len(history_b) == 1 and history_b[0]["partner_id"] == a
    assert history_a[0]["ended_at"] is None  # still an active call


def test_skip_closes_out_the_match(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta, tb = make_token(a), make_token(b)

    client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {tb}"})

    skip_res = client.post("/matching/skip", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    assert skip_res.json()["partner_id"] == str(b)

    history_a = client.get(f"/users/{a}/matches", headers={"Authorization": f"Bearer {ta}"}).json()
    assert history_a[0]["ended_at"] is not None
    assert history_a[0]["duration_seconds"] is not None


def test_blocked_pair_is_not_rematched(client, make_user, make_token):
    """
    Step 9.3 — after a report (which auto-blocks reporter -> reported), the
    two should not be paired together again even if both are the only two
    users in the queue.
    """
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta, tb = make_token(a), make_token(b)

    client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {tb}"})

    client.post(
        "/reports",
        json={"reporter_id": a, "reported_id": b, "reason": "spam"},
        headers={"Authorization": f"Bearer {ta}"},
    )

    client.post("/matching/skip", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    client.post("/matching/skip", json={"tag": None}, headers={"Authorization": f"Bearer {tb}"})

    r_a = client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {ta}"})
    r_b = client.post("/matching/join", json={"tag": None}, headers={"Authorization": f"Bearer {tb}"})

    # Neither call should report a match with each other — both end up waiting
    # (or matched with someone else, but there's no one else here).
    assert r_a.json()["status"] == "waiting"
    assert r_b.json()["status"] == "waiting"
