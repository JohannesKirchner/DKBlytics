from decimal import Decimal

import pytest


def _find_id(client, name):
    """Resolve a category name to its id via /categories/tree."""
    tree = client.get("/api/categories/tree").json()

    def walk(nodes):
        for n in nodes:
            if n["name"] == name:
                return n["id"]
            r = walk(n["children"])
            if r is not None:
                return r
        return None

    return walk(tree)


@pytest.mark.order(56)
def test_budget_sankey_structure(client):
    r = client.get("/api/budget/sankey")
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("nodes", "links", "totals", "meta"):
        assert key in body, f"missing {key}"

    income = Decimal(str(body["totals"]["income"]))
    expenses = Decimal(str(body["totals"]["expenses"]))
    savings = Decimal(str(body["totals"]["savings"]))
    # Savings is the synthetic delta, always exactly income - expenses.
    assert income - expenses == savings
    # The seeded mock data is expense-heavy.
    assert expenses > 0
    assert body["meta"]["months_with_data"] >= 1

    ids = {n["id"] for n in body["nodes"]}
    assert "expenses" in ids
    # Every link references existing nodes and carries a positive magnitude.
    for link in body["links"]:
        assert link["source"] in ids, link
        assert link["target"] in ids, link
        assert Decimal(str(link["value"])) > 0

    # Conservation: flow out of the Expenses hub to its direct children does
    # not exceed the expense total.
    out = sum(
        Decimal(str(link["value"]))
        for link in body["links"]
        if link["source"] == "expenses"
    )
    assert out <= expenses


@pytest.mark.order(57)
def test_budget_sankey_account_filter(client):
    # Filtering by a real account still returns a valid payload.
    accounts = client.get("/api/accounts/").json()
    acct_id = accounts[0]["public_id"]
    r = client.get(f"/api/budget/sankey?account_id={acct_id}")
    assert r.status_code == 200, r.text

    # Date window that excludes everything -> empty-ish but valid.
    r = client.get("/api/budget/sankey?date_from=1999-01-01&date_to=1999-12-31")
    assert r.status_code == 200, r.text
    assert r.json()["meta"]["months_with_data"] == 0


@pytest.mark.order(58)
def test_budget_sankey_bad_requests(client):
    assert client.get("/api/budget/sankey?date_from=not-a-date").status_code == 400
    assert client.get("/api/budget/sankey?account_id=does-not-exist").status_code == 404
    assert (
        client.get("/api/budget/sankey?date_from=2025-06-01&date_to=2025-01-01").status_code
        == 400
    )


@pytest.mark.order(59)
def test_budget_category_series(client):
    rent_id = _find_id(client, "Rent")
    assert rent_id is not None

    r = client.get(f"/api/budget/category-series?category_id={rent_id}")
    assert r.status_code == 200, r.text
    points = r.json()
    assert len(points) >= 1
    for p in points:
        assert "date" in p and "value" in p

    # Monthly buckets are ascending with no gaps, and Rent has a real spend.
    dates = [p["date"] for p in points]
    assert dates == sorted(dates)
    assert any(Decimal(str(p["value"])) > 0 for p in points)

    # Yearly granularity also works.
    ry = client.get(
        f"/api/budget/category-series?category_id={rent_id}&granularity=yearly"
    )
    assert ry.status_code == 200, ry.text


@pytest.mark.order(60)
def test_budget_category_series_special_and_errors(client):
    assert (
        client.get("/api/budget/category-series?category_id=uncategorized").status_code
        == 200
    )
    assert (
        client.get("/api/budget/category-series?category_id=999999").status_code == 404
    )
    assert client.get("/api/budget/category-series?category_id=abc").status_code == 400
    rent_id = _find_id(client, "Rent")
    assert (
        client.get(
            f"/api/budget/category-series?category_id={rent_id}&granularity=weekly"
        ).status_code
        == 400
    )
