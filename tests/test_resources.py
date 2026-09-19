def test_resource_and_skill_link(
    client,
    auth_headers,
):
    skill = client.post(
        "/v1/skills",
        headers=auth_headers,
        json={
            "name": "Transformers",
            "slug": "transformers",
            "category": "AI",
            "current_level": 1,
            "target_level": 4,
            "metadata": {},
        },
    )

    assert skill.status_code == 201

    skill_id = skill.json()["id"]

    resource = client.post(
        "/v1/resources",
        headers=auth_headers,
        json={
            "title": (
                "Attention Is All You Need"
            ),
            "resource_type": "paper",
            "status": "active",
            "url": (
                "https://arxiv.org/abs/"
                "1706.03762"
            ),
            "author": "Vaswani et al.",
            "description": (
                "Transformer architecture paper."
            ),
            "progress_percent": 20,
            "metadata": {
                "test": True
            },
        },
    )

    assert resource.status_code == 201

    resource_id = (
        resource.json()["id"]
    )

    response = client.post(
        (
            f"/v1/resources/{resource_id}"
            f"/skills/{skill_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.get(
        f"/v1/resources/{resource_id}/skills",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert (
        response.json()["data"][0]["id"]
        == skill_id
    )

    response = client.get(
        "/v1/search",
        headers=auth_headers,
        params={
            "q": "Attention"
        },
    )

    assert response.status_code == 200

    assert any(
        item["type"] == "resource"
        for item in response.json()["data"]
    )