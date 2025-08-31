import json
import pytest
from pathlib import Path

with open(Path(__file__).parent / "../data/transactions.json") as f:
    TRANSACTIONS = json.load(f)


@pytest.mark.order(10)
@pytest.mark.parametrize(
    "payload", [pytest.param(p, id=p["text"]) for p in TRANSACTIONS]
)
def test_create_transaction(client, payload):
    response = client.post("/transactions/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(11)
def test_get_transactions(client):
    response = client.get("/transactions/")
    response_data = response.json()

    assert response.status_code == 200
    assert response_data["total"] == len(TRANSACTIONS)


@pytest.mark.order(12)
@pytest.mark.parametrize(
    "payload, id",
    [pytest.param(p, idx + 1, id=p["text"]) for (idx, p) in enumerate(TRANSACTIONS)],
)
def test_get_transaction_by_id(client, payload, id):
    response = client.get(f"/transactions/{id}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["text"] == payload["text"]
    assert response_data["entity"] == payload["entity"]
