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
def test_update_transaction(client):
    """Test updating transaction entity and text while preserving fingerprint."""
    # Get the first transaction
    response = client.get("/api/transactions/1")
    original_tx = response.json()
    
    # Store original values
    original_fingerprint = original_tx["fingerprint"]
    original_entity = original_tx["entity"]
    original_text = original_tx["text"]
    
    # Update transaction
    update_payload = {
        "entity": "Updated Entity",
        "text": "Updated Description"
    }
    
    response = client.put("/api/transactions/1", json=update_payload)
    assert response.status_code == 200, response.text
    
    updated_tx = response.json()
    
    # Verify updates applied
    assert updated_tx["entity"] == "Updated Entity"
    assert updated_tx["text"] == "Updated Description"
    
    # Verify fingerprint preserved
    assert updated_tx["fingerprint"] == original_fingerprint
    
    # Verify other fields unchanged
    assert updated_tx["amount"] == original_tx["amount"]
    assert updated_tx["date"] == original_tx["date"]
    assert updated_tx["account_id"] == original_tx["account_id"]
    
    # Test partial update (entity only)
    partial_payload = {"entity": "Partially Updated Entity"}
    response = client.put("/api/transactions/1", json=partial_payload)
    assert response.status_code == 200, response.text
    
    partially_updated_tx = response.json()
    assert partially_updated_tx["entity"] == "Partially Updated Entity"
    assert partially_updated_tx["text"] == "Updated Description"  # Should remain unchanged
    assert partially_updated_tx["fingerprint"] == original_fingerprint  # Still preserved
    
    # Restore original values for other tests
    restore_payload = {
        "entity": original_entity,
        "text": original_text
    }
    client.put("/api/transactions/1", json=restore_payload)


@pytest.mark.order(40) # needs to be run after category rules are assigned
@pytest.mark.parametrize(
    "query, expected_length",
    [
        pytest.param("depth=1", 2, id="Roots"),
        pytest.param("depth=2", 5, id="RootsChildren"),
        pytest.param(
            "depth=2&date_from=2025-01-01&date_to=2025-02-01",
            2,
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
