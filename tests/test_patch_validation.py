from uuid import uuid4


def test_task_rejects_null_status(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Null patch test",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    task_id = response.json()["id"]

    response = client.patch(
        f"/v1/tasks/{task_id}",
        headers=auth_headers,
        json={
            "status": None,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert (
        body["error"]["code"]
        == "null_not_allowed"
    )

    assert (
        "status"
        in body["error"]["details"]["fields"]
    )


def test_nullable_field_can_be_cleared(
    client,
    auth_headers,
):
    suffix = uuid4().hex[:10]

    response = client.post(
        "/v1/notes",
        headers=auth_headers,
        json={
            "title": (
                "Nullable patch "
                + suffix
            ),
            "content": "Test note",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    note_id = response.json()["id"]

    response = client.patch(
        f"/v1/notes/{note_id}",
        headers=auth_headers,
        json={
            "project_id": None,
        },
    )

    assert response.status_code == 200