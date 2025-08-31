import json
import pytest
from pathlib import Path


with open(Path(__file__).parent / "../data/accounts.json") as f:
    ACCOUNTS = json.load(f)


@pytest.mark.order(1)
@pytest.mark.parametrize("payload", [pytest.param(p, id=p["name"]) for p in ACCOUNTS])
def test_create_account(client, payload):
    response = client.post("/accounts/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(2)
def test_get_accounts(client):
    response = client.get("/accounts/")
    response_data = response.json()

    assert response.status_code == 200
    assert len(response_data) == len(ACCOUNTS)


@pytest.mark.order(3)
@pytest.mark.parametrize("payload", [pytest.param(p, id=p["name"]) for p in ACCOUNTS])
def test_get_account_by_name(client, payload):
    response = client.get(f"/accounts/{payload['name']}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["balance"] == payload["balance"]
