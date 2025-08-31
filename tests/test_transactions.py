"""
Transactions API — happy paths and pagination/sorting.
"""

import pytest
from uuid import uuid4


def _extract_id(resp_json):
    # Be tolerant to different response shapes
    for k in ("transaction_id", "id"):
        if k in resp_json:
            return resp_json[k]
    # Some apps return the whole object; try common shapes
    if (
        isinstance(resp_json, dict)
        and "item" in resp_json
        and isinstance(resp_json["item"], dict)
    ):
        for k in ("transaction_id", "id"):
            if k in resp_json["item"]:
                return resp_json["item"][k]
    return None


def _list_items(client, **params):
    r = client.get("/transactions/", params=params)
    assert r.status_code == 200, r.text
    data = r.json()
    # Paginated shape: { "items": [...], "total": N }
    if isinstance(data, dict) and "items" in data:
        return data["items"], data.get("total")
    # Fallback: raw list
    if isinstance(data, list):
        return data, len(data)
    raise AssertionError(f"Unexpected list shape: {data!r}")


@pytest.mark.order(1)
def test_create_and_get_transaction(client, transaction_payload, ensure_account):
    # 1) Make sure the linked account exists
    ensure_account("Checking")
    acc_lst = client.get("/accounts/").json()
    account = [acc for acc in acc_lst if acc["name"] == "Checking"][0]

    # 2) Create the transaction
    payload = transaction_payload(
        text="Flat white",
        entity="Coffee Fellows",
        amount="-3.80",  # string works nicely with Decimal
        reference=str(uuid4()),  # uniqueness to avoid dup fingerprint
        account_id=account["id"],
    )
    r = client.post("/transactions/", json=payload)
    assert r.status_code in (200, 201), r.text
    created = r.json()

    # 3) Fetch it back (be tolerant to id key naming)
    tx_id = created.get("id") or created.get("transaction_id")
    assert tx_id, f"Unexpected response shape: {created}"
    r = client.get(f"/transactions/{tx_id}")
    assert r.status_code == 200, r.text
    got = r.json()
    assert got["entity"] == "Coffee Fellows"
    assert str(got["amount"]).startswith("-3.8")


@pytest.mark.order(2)
def test_list_sort_and_filters(client, transaction_payload, ensure_account):
    # 1) Make sure the linked account exists
    ensure_account("Checking")

    # Create a few transactions
    client.post(
        "/transactions/",
        json=transaction_payload(
            text="Groceries at REWE", entity="REWE", amount="-25.00", days_ago=3
        ),
    )
    client.post(
        "/transactions/",
        json=transaction_payload(
            text="Train ticket", entity="DB Bahn", amount="-49.90", days_ago=2
        ),
    )
    client.post(
        "/transactions/",
        json=transaction_payload(
            text="Salary", entity="Employer GmbH", amount="2500.00", days_ago=10
        ),
    )

    # Default list
    items, total = _list_items(client)
    assert len(items) >= 3

    # Filter by text (contains)
    items, _ = _list_items(client, text="Groceries at REWE")
    assert any("REWE" in i.get("entity", "") for i in items)

    # Filter by entity
    items, _ = _list_items(client, entity="DB Bahn")
    print(items)
    assert all(i.get("entity") == "DB Bahn" for i in items)

    # Sort ascending by date
    items, _ = _list_items(client, sort_by="date_asc", limit=2)
    assert len(items) <= 2
    if len(items) == 2:
        assert items[0]["date"] <= items[1]["date"]
