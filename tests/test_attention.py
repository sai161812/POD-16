def test_attention_view_uses_rules(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/rules",
        headers=auth_headers,
        json={
            "name": (
                "Critical task attention"
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
                    "type": "score",
                    "value": 50,
                },
                {
                    "type": "label",
                    "value": "urgent",
                },
                {
                    "type": "message",
                    "value": (
                        "Critical task needs "
                        "attention."
                    ),
                },
            ],
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": (
                "Attention test task"
            ),
            "status": "todo",
            "priority": "critical",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    task_id = response.json()["id"]

    response = client.get(
        "/v1/attention",
        headers=auth_headers,
        params={
            "domain": "task"
        },
    )

    assert response.status_code == 200

    payload = response.json()

    matching = [
        item
        for item in payload["data"]
        if item["entity_id"]
        == task_id
    ]

    assert len(matching) == 1

    item = matching[0]

    assert (
        item["requires_attention"]
        is True
    )

    assert item["score"] >= 50

    assert "urgent" in item["labels"]

    # Change the fact that caused
    # the rule to match.
    response = client.patch(
        f"/v1/tasks/{task_id}",
        headers=auth_headers,
        json={
            "priority": "normal"
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/attention",
        headers=auth_headers,
        params={
            "domain": "task"
        },
    )

    assert response.status_code == 200

    matching = [
        item
        for item
        in response.json()["data"]
        if item["entity_id"]
        == task_id
    ]

    assert matching == []