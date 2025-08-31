"""
Categories API — create/list and rule updates.
"""

import pytest


def _get_categories(client):
    r = client.get("/categories/")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.order(10)
def test_create_and_list_categories(client, unique_name):
    # Some FastAPI signatures use query params for simple POST args; prefer params here.
    r = client.post("/categories/", params={"name": unique_name})
    assert r.status_code in (200, 201), r.text
    created = r.json()
    assert created["name"] == unique_name
    cat_id = created["id"]

    cats = _get_categories(client)
    assert any(c["id"] == cat_id for c in cats)


@pytest.mark.order(11)
def test_update_rule_by_entity_404_when_missing(client, unique_name):
    # Update a non-existing rule by entity should return 404
    r = client.patch(
        f"/categories/rules/by-entity/{unique_name}", params={"category_id": 1}
    )
    assert r.status_code in (404, 422), r.text  # 422 if validation blocks, else 404
