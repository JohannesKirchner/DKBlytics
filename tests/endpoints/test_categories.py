import json
import pytest
from pathlib import Path


with open(Path(__file__).parent / "../mock_data/categories.json") as f:
    CATEGORIES = json.load(f)


@pytest.mark.order(20)
@pytest.mark.parametrize("payload", [pytest.param(c, id=c["name"]) for c in CATEGORIES])
def test_create_category(client, payload):
    response = client.post("/categories/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(21)
def test_get_categories(client):
    response = client.get("/categories/")
    response_data = response.json()

    assert response.status_code == 200
    assert len(response_data) == len(CATEGORIES)


@pytest.mark.order(22)
@pytest.mark.parametrize(
    "payload",
    [pytest.param(c, id=c["name"]) for c in CATEGORIES],
)
def test_get_category_by_name(client, payload):
    response = client.get(f"/categories/{payload["name"]}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["parent_name"] == payload["parent_name"]


@pytest.mark.order(23)
@pytest.mark.parametrize(
    "category_name",
    [
        pytest.param(None, id="No_Category_Name"),
        pytest.param("Expense", id="Expense"),
        pytest.param("Mobility", id="Mobility"),
    ],
)
def test_get_category_tree(client, category_name):
    if category_name is None:
        response = client.get("/categories/tree")
    else:
        response = client.get(f"/categories/tree?name={category_name}")
    response_data = response.json()

    assert response.status_code == 200, response.text

    expected_categories = [c for c in CATEGORIES if c["parent_name"] == category_name]
    assert len(expected_categories) == len(response_data)
