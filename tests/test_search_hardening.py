from uuid import uuid4


def test_search_includes_skills(
    client,
    auth_headers,
):
    suffix = uuid4().hex[:10]

    name = (
        "SearchSkill "
        + suffix
    )

    response = client.post(
        "/v1/skills",
        headers=auth_headers,
        json={
            "name": name,
            "slug": (
                "search-skill-"
                + suffix
            ),
            "category": "testing",
            "current_level": 1,
            "target_level": 3,
            "metadata": {},
        },
    )

    assert response.status_code == 201

    skill_id = response.json()["id"]

    response = client.get(
        "/v1/search",
        headers=auth_headers,
        params={
            "q": suffix,
        },
    )

    assert response.status_code == 200

    results = response.json()["data"]

    assert any(
        item["type"] == "skill"
        and item["id"] == skill_id
        for item in results
    )


def test_percent_is_literal_search(
    client,
    auth_headers,
):
    suffix = uuid4().hex[:10]

    special = client.post(
        "/v1/notes",
        headers=auth_headers,
        json={
            "title": (
                f"Coverage 100% {suffix}"
            ),
            "content": (
                "Contains a literal percent."
            ),
            "metadata": {},
        },
    )

    assert special.status_code == 201

    special_id = special.json()["id"]

    plain = client.post(
        "/v1/notes",
        headers=auth_headers,
        json={
            "title": (
                f"Plain note {suffix}"
            ),
            "content": (
                "No special symbol here."
            ),
            "metadata": {},
        },
    )

    assert plain.status_code == 201

    plain_id = plain.json()["id"]

    response = client.get(
        "/v1/search",
        headers=auth_headers,
        params={
            "q": "%",
            "limit": 100,
        },
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item
        in response.json()["data"]
    }

    assert special_id in ids
    assert plain_id not in ids