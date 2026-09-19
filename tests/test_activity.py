from uuid import uuid4


def test_activity_records_mutations(
    client,
    auth_headers,
):
    slug = (
        "audit-test-"
        + uuid4().hex[:12]
    )

    response = client.post(
        "/v1/projects",
        headers=auth_headers,
        json={
            "name": "Audit Test",
            "slug": slug,
            "status": "active",
            "priority": "normal",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    project_id = (
        response.json()["id"]
    )

    response = client.patch(
        f"/v1/projects/{project_id}",
        headers=auth_headers,
        json={
            "progress_percent": 42,
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/activity",
        headers=auth_headers,
        params={
            "domain": "projects",
            "limit": 20,
        },
    )

    assert response.status_code == 200

    events = response.json()["data"]

    assert any(
        event["operation"]
        == "POST /v1/projects"
        for event in events
    )

    update_events = [
        event
        for event in events
        if event["operation"]
        == (
            "PATCH "
            "/v1/projects/{project_id}"
        )
    ]

    assert update_events

    update_event = update_events[0]

    assert (
        update_event["entity_id"]
        == project_id
    )

    assert (
        update_event["actor_name"]
        == "bootstrap"
    )

    assert (
        update_event["request_id"]
        is not None
    )