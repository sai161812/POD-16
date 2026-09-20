from uuid import uuid4


def test_project_restore(
    client,
    auth_headers,
):
    slug = (
        "restore-project-"
        + uuid4().hex[:10]
    )

    response = client.post(
        "/v1/projects",
        headers=auth_headers,
        json={
            "name": "Restore Project",
            "slug": slug,
            "status": "active",
            "priority": "normal",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    project_id = response.json()["id"]

    response = client.delete(
        f"/v1/projects/{project_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.get(
        f"/v1/projects/{project_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    response = client.post(
        f"/v1/projects/{project_id}/restore",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_cannot_delete_active_prerequisite(
    client,
    auth_headers,
):
    prerequisite = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Prerequisite",
            "status": "todo",
            "priority": "normal",
            "metadata": {},
        },
    )

    assert prerequisite.status_code == 201

    prerequisite_id = (
        prerequisite.json()["id"]
    )

    dependent = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Dependent",
            "status": "todo",
            "priority": "normal",
            "metadata": {},
        },
    )

    assert dependent.status_code == 201

    dependent_id = dependent.json()["id"]

    response = client.post(
        (
            f"/v1/tasks/{dependent_id}"
            f"/dependencies/"
            f"{prerequisite_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.delete(
        f"/v1/tasks/{prerequisite_id}",
        headers=auth_headers,
    )

    assert response.status_code == 409

    assert (
        response.json()["error"]["code"]
        == "task_has_active_dependents"
    )

    response = client.delete(
        (
            f"/v1/tasks/{dependent_id}"
            f"/dependencies/"
            f"{prerequisite_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.delete(
        f"/v1/tasks/{prerequisite_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204