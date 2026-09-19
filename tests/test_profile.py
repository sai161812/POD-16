def test_profile_defaults_and_update(
    client,
    auth_headers,
):
    response = client.get(
        "/v1/profile",
        headers=auth_headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["timezone"] == "Asia/Kolkata"
    assert payload["locale"] == "en-IN"

    response = client.patch(
        "/v1/profile",
        headers=auth_headers,
        json={
            "display_name": "Sai",
            "about": (
                "AI, systems and cybersecurity."
            ),
            "preferences": {
                "assistant": {
                    "verbosity": "concise",
                    "confirm_destructive_actions": True,
                },
                "planning": {
                    "default_task_priority": "normal",
                },
            },
            "metadata": {
                "source": "test",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["display_name"] == "Sai"

    assert (
        payload["preferences"]
        ["assistant"]
        ["confirm_destructive_actions"]
        is True
    )


def test_profile_scope_enforcement(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/clients",
        headers=auth_headers,
        json={
            "name": "Profile Reader",
            "scopes": [
                "profile:read",
            ],
        },
    )

    assert response.status_code == 201

    api_key = response.json()[
        "api_key"
    ]

    headers = {
        "Authorization": (
            f"Bearer {api_key}"
        )
    }

    response = client.get(
        "/v1/profile",
        headers=headers,
    )

    assert response.status_code == 200

    response = client.patch(
        "/v1/profile",
        headers=headers,
        json={
            "display_name": "Nope"
        },
    )

    assert response.status_code == 403