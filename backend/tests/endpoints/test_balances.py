import json
from decimal import Decimal
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "../mock_data"


@pytest.fixture(scope="module", autouse=True)
def seed_balances_data(client):
    # If accounts already exist (full suite), skip seeding.
    if client.get("/api/accounts/").json():
        return

    with (DATA_DIR / "accounts.json").open() as fh:
        accounts = json.load(fh)
    for payload in accounts:
        resp = client.post("/api/accounts/", json=payload)
        assert resp.status_code == 201, resp.text

    with (DATA_DIR / "transactions.json").open() as fh:
        transactions = json.load(fh)
    for payload in transactions:
        resp = client.get(f"/api/accounts?name={payload['account_name']}")
        account = resp.json()[0]
        tx_payload = dict(payload)
        tx_payload["account_id"] = account["public_id"]
        tx_payload.pop("account_name", None)
        resp = client.post("/api/transactions/", json=tx_payload)
        assert resp.status_code == 201, resp.text


@pytest.mark.order(50)
def test_balance_series_daily_combined(client):
    response = client.get(
        "/api/balances/series?date_from=2025-01-01&date_to=2025-01-15"
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 15

    assert data[0]["date"] == "2025-01-01"
    assert Decimal(data[0]["balance"]) == Decimal("11958.35")

    jan_11 = next(point for point in data if point["date"] == "2025-01-11")
    assert Decimal(jan_11["balance"]) == Decimal("11877.85")

    assert data[-1]["date"] == "2025-01-15"
    assert Decimal(data[-1]["balance"]) == Decimal("11877.85")


@pytest.mark.order(51)
def test_balance_series_weekly_account(client):
    account_response = client.get("/api/accounts?name=Girokonto")
    account_id = account_response.json()[0]["public_id"]

    response = client.get(
        f"/api/balances/series?granularity=weekly&account_id={account_id}"
        "&date_from=2025-01-01&date_to=2025-01-31"
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 5

    assert data[0]["date"] == "2025-01-05"
    assert Decimal(data[0]["balance"]) == Decimal("1958.35")

    assert data[-1]["date"] == "2025-01-31"
    assert Decimal(data[-1]["balance"]) == Decimal("1828.62")


@pytest.mark.order(52)
def test_surplus_daily_combined(client):
    response = client.get(
        "/api/balances/surplus?date_from=2025-01-01&date_to=2025-01-15"
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 15

    jan_11 = next(point for point in data if point["date"] == "2025-01-11")
    assert Decimal(jan_11["delta"]) == Decimal("-80.50")

    jan_02 = next(point for point in data if point["date"] == "2025-01-02")
    assert Decimal(jan_02["delta"]) == Decimal("0.00")


@pytest.mark.order(53)
def test_surplus_monthly_combined(client):
    response = client.get(
        "/api/balances/surplus?granularity=monthly&date_from=2025-01-01&date_to=2025-01-31"
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 1
    assert data[0]["date"] == "2025-01-31"
    assert Decimal(data[0]["delta"]) == Decimal("-129.73")


@pytest.mark.order(54)
def test_balance_series_yearly(client):
    response = client.get(
        "/api/balances/series?granularity=yearly&date_from=2025-01-01&date_to=2025-05-31"
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 1
    assert data[0]["date"] == "2025-05-31"
    assert Decimal(data[0]["balance"]) == Decimal("10000.00")


@pytest.mark.order(55)
def test_balance_series_fiscal_monthly(client):
    response = client.get(
        "/api/balances/series?granularity=fiscal_monthly&date_from=2025-01-01&date_to=2025-05-31"
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) >= 4  # spans multiple fiscal months
    assert data[0]["date"] == "2025-01-14"  # first fiscal bucket closes Jan 6
    assert data[1]["date"] == "2025-02-14"
    assert data[-1]["date"] == "2025-05-31"
