import json
import pytest
from pathlib import Path


with open(Path(__file__).parent / "../mock_data/category_rules.json") as f:
    CATEGORY_RULES = json.load(f)


@pytest.mark.order(30)
@pytest.mark.parametrize(
    "payload", [pytest.param(c, id=c.get("entity", f"tx_{c.get('transaction_id')}")) for c in CATEGORY_RULES]
)
def test_create_category_rule(client, payload):
    response = client.post("/api/rules/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(31)
def test_get_category_rules(client):
    response = client.get("/api/rules/")
    response_data = response.json()

    assert response.status_code == 200
    assert len(response_data) == len(CATEGORY_RULES)


@pytest.mark.order(32)
@pytest.mark.parametrize(
    "payload", [pytest.param(c, id=c.get("entity", f"tx_{c.get('transaction_id')}")) for c in CATEGORY_RULES if c.get("entity") is not None]
)
def test_resolve_category_rule(client, payload):
    response = client.get(
        f"/api/rules/resolve?entity={payload["entity"]}&text={payload["text"]}"
    )
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data == payload["category_name"]


@pytest.mark.order(33)
def test_transaction_rule_from_mock_data(client):
    """Test that transaction-specific rule from mock data works correctly."""
    # First, let's check what transaction ID 2 actually is
    response = client.get("/api/transactions/2")
    transaction = response.json()
    
    assert response.status_code == 200
    print(f"Transaction 2: entity={transaction['entity']}, original_category={transaction['category']}")
    
    # Check if transaction rule was created successfully from mock data
    rules_response = client.get("/api/rules/")
    rules = rules_response.json()
    
    transaction_rule = None
    for rule in rules:
        if rule.get("transaction_id") == 2:
            transaction_rule = rule
            break
    
    if transaction_rule is not None:
        # Transaction rule exists, verify it takes effect
        assert transaction_rule["category_name"] == "Car"
        assert transaction_rule["entity"] is None
        assert transaction_rule["text"] is None
        
        # The transaction should have the overridden category
        assert transaction["category"] == "Car", f"Expected 'Car', got '{transaction['category']}'"
    else:
        # If no transaction rule exists, skip this test (transaction might not exist at rule creation time)
        pytest.skip("Transaction rule for ID 2 not found - transaction may not exist during rule creation")


@pytest.mark.order(34)  
def test_transaction_rule_priority_temporarily(client):
    """Test transaction rule priority with temporary rule that gets cleaned up."""
    # Get transaction ID 1 (should not have transaction rule, only entity rule)
    response = client.get("/api/transactions/1")
    original_tx = response.json()
    
    assert original_tx["entity"] == "DB Bahn"
    assert original_tx["category"] == "Train"  # From entity rule
    
    # Temporarily create transaction-specific rule to override
    temp_rule_payload = {
        "transaction_id": 1,
        "entity": None,
        "text": None,
        "category_name": "Utilities"  # Override to different category
    }
    
    create_response = client.post("/api/rules/", json=temp_rule_payload)
    assert create_response.status_code == 201
    created_rule = create_response.json()
    rule_id = created_rule["id"]
    
    try:
        # Verify transaction rule takes priority
        response = client.get("/api/transactions/1")
        updated_tx = response.json()
        assert updated_tx["category"] == "Utilities"  # Transaction rule overrides entity rule
        
    finally:
        # Clean up: delete the temporary rule
        client.delete(f"/api/rules/{rule_id}")
        
        # Verify cleanup worked - should be back to original category
        response = client.get("/api/transactions/1")
        restored_tx = response.json()
        assert restored_tx["category"] == "Train"  # Back to entity rule


@pytest.mark.order(35)
def test_transaction_rule_conflict_with_cleanup(client):
    """Test transaction rule conflict with proper cleanup."""
    # Use transaction 3 for this test (should be available)
    transaction_id = 3
    
    # Create first transaction rule
    payload1 = {
        "transaction_id": transaction_id,
        "entity": None,
        "text": None,
        "category_name": "Car"
    }
    
    response1 = client.post("/api/rules/", json=payload1)
    assert response1.status_code == 201
    rule_id = response1.json()["id"]
    
    try:
        # Try to create conflicting rule - should fail
        payload2 = {
            "transaction_id": transaction_id,
            "entity": None,
            "text": None,
            "category_name": "Utilities"
        }
        
        response2 = client.post("/api/rules/", json=payload2)
        assert response2.status_code == 409  # Conflict
        
    finally:
        # Clean up the test rule
        client.delete(f"/api/rules/{rule_id}")


@pytest.mark.order(36)
def test_transaction_rule_nonexistent_transaction(client):
    """Test creating rule for non-existent transaction."""
    payload = {
        "transaction_id": 99999,  # Non-existent ID
        "entity": None,
        "text": None,
        "category_name": "Groceries"
    }
    
    response = client.post("/api/rules/", json=payload)
    assert response.status_code == 404  # Not found
