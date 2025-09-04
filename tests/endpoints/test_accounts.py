import json
import pytest
from pathlib import Path


with open(Path(__file__).parent / "../mock_data/accounts.json") as f:
    ACCOUNTS = json.load(f)


@pytest.mark.order(1)
@pytest.mark.parametrize("payload", [pytest.param(p, id=p["name"]) for p in ACCOUNTS])
def test_create_account(client, payload):
    response = client.post("/api/accounts/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(2)
def test_get_accounts(client):
    response = client.get("/api/accounts/")
    response_data = response.json()

    assert response.status_code == 200
    assert len(response_data) == len(ACCOUNTS)


@pytest.mark.order(3)
@pytest.mark.parametrize("payload", [pytest.param(p, id=p["name"]) for p in ACCOUNTS])
def test_get_account_by_public_id(client, payload):
    response = client.get(
        f"/api/accounts?name={payload['name']}&holder={payload['holder_name']}"
    )

    assert response.status_code == 200, response.text

    payload = response.json()[0]
    response = client.get(f"/api/accounts/{payload['public_id']}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["balance"] == payload["balance"]
