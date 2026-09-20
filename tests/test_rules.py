def test_task_rule_evaluation(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/rules",
        headers=auth_headers,
        json={
            "name": (
                "Critical todo attention"
            ),
            "description": (
                "Flag critical tasks "
                "that have not started."
            ),
            "domain": "task",
            "match_mode": "all",
            "conditions": [
                {
                    "field": "priority",
                    "operator": "eq",
                    "value": "critical",
                },
                {
                    "field": "status",
                    "operator": "eq",
                    "value": "todo",
                },
            ],
            "effects": [
                {
                    "type": "attention",
                    "value": True,
                },
                {
                    "type": "label",
                    "value": "critical-todo",
                },
                {
                    "type": "score",
                    "value": 40,
                },
                {
                    "type": "message",
                    "value": (
                        "Critical task "
                        "has not been started."
                    ),
                },
            ],
            "enabled": True,
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": (
                "Critical rule test"
            ),
            "status": "todo",
            "priority": "critical",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    task_id = response.json()["id"]

    response = client.get(
        (
            "/v1/rules/evaluate/"
            f"task/{task_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result["requires_attention"]
        is True
    )

    assert (
        "critical-todo"
        in result["labels"]
    )

    assert result["score"] == 40

    assert len(
        result["matched_rules"]
    ) == 1

    # Change the underlying fact.
    response = client.patch(
        f"/v1/tasks/{task_id}",
        headers=auth_headers,
        json={
            "priority": "normal"
        },
    )

    assert response.status_code == 200

    # Same rule, same task ID,
    # different facts -> different consequence.
    response = client.get(
        (
            "/v1/rules/evaluate/"
            f"task/{task_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result["requires_attention"]
        is False
    )

    assert result["score"] == 0

    assert result["matched_rules"] == []