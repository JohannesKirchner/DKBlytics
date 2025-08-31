import json
import pytest
from pathlib import Path


with open(Path(__file__).parent / "../data/category_rules.json") as f:
    CATEGORY_RULES = json.load(f)


@pytest.mark.order(30)
@pytest.mark.parametrize(
    "payload", [pytest.param(c, id=c["entity"]) for c in CATEGORY_RULES]
)
def test_create_category_rule(client, payload):
    response = client.post("/category-rules/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(31)
def test_get_category_rules(client):
    response = client.get("/category-rules/")
    response_data = response.json()

    assert response.status_code == 200
    assert len(response_data) == len(CATEGORY_RULES)


@pytest.mark.order(32)
@pytest.mark.parametrize(
    "payload, id",
    [
        pytest.param(c, idx + 1, id=c["entity"])
        for (idx, c) in enumerate(CATEGORY_RULES)
    ],
)
def test_get_category_rule_by_id(client, payload, id):
    response = client.get(f"/category-rules/{id}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["category_name"] == payload["category_name"]
