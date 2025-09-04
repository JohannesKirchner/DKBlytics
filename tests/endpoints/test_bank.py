"""
Bank integration endpoint — ensure we can hit it with a mocked service.
"""

import pytest


@pytest.mark.order(40)
def test_update_from_bank(client, monkeypatch):
    # Patch the bank service to avoid real network calls
    # The router calls services.bank.get_new_transactions(db)
    import src.routers.bank as bank_router

    def fake_get_new_transactions(db):
        # Return a defaultdict-like or dict mapping account names to counts

        return {"Checking": 2, "Savings": 1}

    monkeypatch.setattr(bank_router, "get_new_transactions", fake_get_new_transactions)

    r = client.post("/api/bank/update_from_bank/")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)
    assert "Bank update completed." in data.get("message", "")
    assert "Checking" in data["inserted"] and "Savings" in data["inserted"]
