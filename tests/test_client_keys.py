def test_client_key_scopes_and_revocation(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/clients",
        headers=auth_headers,
        json={
            "name": "Read Only Agent",
            "scopes": [
                "tasks:read",
            ],
        },
    )

    assert response.status_code == 201

    payload = response.json()

    client_id = payload["id"]
    api_key = payload["api_key"]

    scoped_headers = {
        "Authorization": (
            f"Bearer {api_key}"
        )
    }

    # Read is allowed.
    response = client.get(
        "/v1/tasks",
        headers=scoped_headers,
    )

    assert response.status_code == 200

    # Write is forbidden.
    response = client.post(
        "/v1/tasks",
        headers=scoped_headers,
        json={
            "title": "Should not exist",
        },
    )

    assert response.status_code == 403

    assert (
        response.json()["error"]["code"]
        == "insufficient_scope"
    )

    # Raw key must not appear in listings.
    response = client.get(
        "/v1/clients",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert api_key not in response.text

    # Revoke it.
    response = client.delete(
        f"/v1/clients/{client_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Revoked key is rejected.
    response = client.get(
        "/v1/tasks",
        headers=scoped_headers,
    )

    assert response.status_code == 401

    assert (
        response.json()["error"]["code"]
        == "api_key_revoked"
    )