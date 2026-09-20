from uuid import uuid4


def test_note_offset_pagination(
    client,
    auth_headers,
):
    suffix = uuid4().hex[:10]

    created_ids = set()

    for index in range(3):
        response = client.post(
            "/v1/notes",
            headers=auth_headers,
            json={
                "title": (
                    f"Pagination {suffix} "
                    f"{index}"
                ),
                "content": (
                    "Pagination test."
                ),
                "metadata": {},
            },
        )

        assert response.status_code == 201

        created_ids.add(
            response.json()["id"]
        )

    first = client.get(
        "/v1/notes",
        headers=auth_headers,
        params={
            "q": suffix,
            "limit": 2,
            "offset": 0,
        },
    )

    assert first.status_code == 200

    first_ids = {
        item["id"]
        for item
        in first.json()["data"]
    }

    assert len(first_ids) == 2

    second = client.get(
        "/v1/notes",
        headers=auth_headers,
        params={
            "q": suffix,
            "limit": 2,
            "offset": 2,
        },
    )

    assert second.status_code == 200

    second_ids = {
        item["id"]
        for item
        in second.json()["data"]
    }

    assert len(second_ids) == 1

    assert first_ids.isdisjoint(
        second_ids
    )

    assert (
        first_ids | second_ids
        == created_ids
    )


def test_negative_offset_rejected(
    client,
    auth_headers,
):
    response = client.get(
        "/v1/tasks",
        headers=auth_headers,
        params={
            "offset": -1,
        },
    )

    assert response.status_code == 422