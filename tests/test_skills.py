def test_skill_learning_progress(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/skills",
        headers=auth_headers,
        json={
            "name": "Machine Learning",
            "slug": "machine-learning",
            "category": "AI",
            "current_level": 2,
            "target_level": 4,
            "notes": "Build toward advanced ML.",
            "metadata": {
                "test": True,
            },
        },
    )

    assert response.status_code == 201

    skill_id = response.json()["id"]

    response = client.post(
        f"/v1/skills/{skill_id}/sessions",
        headers=auth_headers,
        json={
            "minutes": 90,
            "summary": "Neural networks",
            "source": "study",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    response = client.post(
        f"/v1/skills/{skill_id}/sessions",
        headers=auth_headers,
        json={
            "minutes": 60,
            "summary": "Attention mechanisms",
            "source": "study",
            "metadata": {},
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/v1/skills/{skill_id}/progress",
        headers=auth_headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["session_count"] == 2
    assert payload["total_minutes"] == 150
    assert payload["current_level"] == 2
    assert payload["target_level"] == 4
    assert payload["level_gap"] == 2