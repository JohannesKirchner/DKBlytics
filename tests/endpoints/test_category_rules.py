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
    response = client.post("/rules/", json=payload)

    assert response.status_code == 201, response.text


@pytest.mark.order(31)
def test_get_category_rules(client):
    response = client.get("/rules/")
    response_data = response.json()

    assert response.status_code == 200
    assert len(response_data) == len(CATEGORY_RULES)


@pytest.mark.order(32)
@pytest.mark.parametrize(
    "payload", [pytest.param(c, id=c["entity"]) for c in CATEGORY_RULES]
)
def test_resolve_category_rule(client, payload):
    response = client.get(
        f"/rules/resolve?entity={payload["entity"]}&text={payload["text"]}"
    )
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data == payload["category_name"]
