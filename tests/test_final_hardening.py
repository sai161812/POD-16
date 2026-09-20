from uuid import uuid4


def test_project_parent_cycle_rejected(
    client,
    auth_headers,
):
    suffix = uuid4().hex[:8]

    first = client.post(
        "/v1/projects",
        headers=auth_headers,
        json={
            "name": "Parent A",
            "slug": f"parent-a-{suffix}",
            "metadata": {},
        },
    )

    assert first.status_code == 201
    first_id = first.json()["id"]

    second = client.post(
        "/v1/projects",
        headers=auth_headers,
        json={
            "name": "Parent B",
            "slug": f"parent-b-{suffix}",
            "parent_project_id": first_id,
            "metadata": {},
        },
    )

    assert second.status_code == 201
    second_id = second.json()["id"]

    response = client.patch(
        f"/v1/projects/{first_id}",
        headers=auth_headers,
        json={
            "parent_project_id": second_id,
        },
    )

    assert response.status_code == 422

    assert (
        response.json()["error"]["code"]
        == "project_parent_cycle"
    )


def test_completed_goal_stays_100_percent(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/goals",
        headers=auth_headers,
        json={
            "title": "Completed goal",
            "status": "completed",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    goal_id = response.json()["id"]

    response = client.patch(
        f"/v1/goals/{goal_id}",
        headers=auth_headers,
        json={
            "progress_percent": 25,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["progress_percent"]
        == 100
    )


def test_profile_nullable_field_can_clear(
    client,
    auth_headers,
):
    response = client.patch(
        "/v1/profile",
        headers=auth_headers,
        json={
            "about": "Temporary value",
        },
    )

    assert response.status_code == 200

    response = client.patch(
        "/v1/profile",
        headers=auth_headers,
        json={
            "about": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["about"] is None


def test_long_request_id_is_replaced(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/tasks",
        headers={
            **auth_headers,
            "X-Request-ID": "x" * 500,
        },
        json={
            "title": "Request ID test",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    request_id = response.headers[
        "X-Request-ID"
    ]

    assert len(request_id) <= 128
    assert request_id != "x" * 500