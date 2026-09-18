import os


def test_create_report(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta = make_token(a)

    res = client.post(
        "/reports",
        json={"reporter_id": a, "reported_id": b, "reason": "harassment", "details": "was rude"},
        headers={"Authorization": f"Bearer {ta}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "reported"


def test_cannot_file_report_as_someone_else(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    tb = make_token(b)  # bob's own token

    # bob tries to file a report claiming to be alice (reporter_id=a)
    res = client.post(
        "/reports",
        json={"reporter_id": a, "reported_id": b, "reason": "spam"},
        headers={"Authorization": f"Bearer {tb}"},
    )
    assert res.status_code == 403


def test_auto_suspend_after_threshold(client, make_user, make_token):
    a = make_user(1, "alice")
    b = make_user(2, "bob")
    ta = make_token(a)

    results = []
    for _ in range(3):
        res = client.post(
            "/reports",
            json={"reporter_id": a, "reported_id": b, "reason": "spam"},
            headers={"Authorization": f"Bearer {ta}"},
        )
        results.append(res.json())

    assert results[0]["auto_suspended"] is False
    assert results[1]["auto_suspended"] is False
    assert results[2]["auto_suspended"] is True


def test_reports_list_blocked_for_non_admin(client, make_user, make_token, monkeypatch):
    monkeypatch.setenv("ADMIN_GITHUB_USERNAMES", "realadmin")
    a = make_user(1, "alice")
    ta = make_token(a, github_username="alice")

    res = client.get("/reports", headers={"Authorization": f"Bearer {ta}"})
    assert res.status_code == 403


def test_reports_list_allowed_for_admin(client, make_token, monkeypatch):
    monkeypatch.setenv("ADMIN_GITHUB_USERNAMES", "realadmin")
    admin_token = make_token(1, github_username="realadmin")

    res = client.get("/reports", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200


def test_no_token_is_unauthorized(client):
    res = client.get("/reports")
    assert res.status_code == 401
