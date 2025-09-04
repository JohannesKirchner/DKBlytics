import json
import pytest
from pathlib import Path

with open(Path(__file__).parent / "../mock_data/transactions.json") as f:
    TRANSACTIONS = json.load(f)


@pytest.mark.order(10)
@pytest.mark.parametrize(
    "payload", [pytest.param(p, id=p["text"]) for p in TRANSACTIONS]
)
def test_create_transaction(client, payload):
    # get public id and replace the account name with it
    response = client.get(f"/api/accounts?name={payload['account_name']}")
    acct_payload = response.json()[0]
    del payload["account_name"]
    payload["account_id"] = acct_payload["public_id"]

    response = client.post("/api/transactions/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(11)
def test_get_transactions(client):
    response = client.get("/api/transactions/")
    response_data = response.json()

    assert response.status_code == 200
    assert response_data["total"] == len(TRANSACTIONS)


@pytest.mark.order(12)
@pytest.mark.parametrize(
    "payload, id",
    [pytest.param(p, idx + 1, id=p["text"]) for (idx, p) in enumerate(TRANSACTIONS)],
)
def test_get_transaction_by_id(client, payload, id):
    response = client.get(f"/api/transactions/{id}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["text"] == payload["text"]
    assert response_data["entity"] == payload["entity"]


@pytest.mark.order(13)
@pytest.mark.parametrize(
    "query, expected_length",
    [
        pytest.param("depth=1", 2, id="Roots"),
        pytest.param("depth=2", 5, id="RootsChildren"),
        pytest.param(
            "depth=2&date_from=2025-01-01&date_to=2025-02-01",
            3,
            id="RootsChildrenJanuary2025",
        ),
        pytest.param("scope_name=Expense&depth=1", 4, id="Expense"),
        pytest.param("scope_name=Expense&depth=2", 5, id="ExpenseChildren"),
    ],
)
def test_get_transaction_summary(client, query, expected_length):
    response = client.get(f"/api/transactions/summary?{query}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert len(response_data) == expected_length
