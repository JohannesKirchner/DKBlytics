import json
import pytest
from pathlib import Path


with open(Path(__file__).parent / "../mock_data/categories.json") as f:
    CATEGORIES = json.load(f)

SEEDED_ROOTS = ("Einnahmen", "Ausgaben")


def _find_id(client, name):
    """Walk /tree to resolve a category name to its id. Used by tests since
    the API is id-only and mock-data is name-based for human readability."""
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


@pytest.mark.order(20)
@pytest.mark.parametrize("payload", [pytest.param(c, id=c["name"]) for c in CATEGORIES])
def test_create_category(client, payload):
    body = {"name": payload["name"]}
    if payload["parent_name"] is not None:
        parent_id = _find_id(client, payload["parent_name"])
        assert parent_id is not None, f"parent '{payload['parent_name']}' not found"
        body["parent_id"] = parent_id

    response = client.post("/api/categories/", json=body)
    assert response.status_code == 201, response.text


@pytest.mark.order(21)
def test_get_categories(client):
    response = client.get("/api/categories/")
    response_data = response.json()

    assert response.status_code == 200
    # +N for the auto-seeded root categories.
    assert len(response_data) == len(CATEGORIES) + len(SEEDED_ROOTS)


@pytest.mark.order(22)
@pytest.mark.parametrize(
    "payload",
    [pytest.param(c, id=c["name"]) for c in CATEGORIES],
)
def test_get_category_by_id(client, payload):
    cat_id = _find_id(client, payload["name"])
    assert cat_id is not None

    response = client.get(f"/api/categories/{cat_id}")
    response_data = response.json()

    assert response.status_code == 200, response.text
    assert response_data["name"] == payload["name"]
    assert response_data["parent_name"] == payload["parent_name"]


@pytest.mark.order(23)
@pytest.mark.parametrize(
    "parent_name",
    [
        pytest.param(None, id="No_Parent"),
        pytest.param("Ausgaben", id="Ausgaben"),
        pytest.param("Mobility", id="Mobility"),
    ],
)
def test_get_category_tree(client, parent_name):
    if parent_name is None:
        response = client.get("/api/categories/tree")
    else:
        parent_id = _find_id(client, parent_name)
        assert parent_id is not None
        response = client.get(f"/api/categories/tree?parent_id={parent_id}")
    response_data = response.json()

    assert response.status_code == 200, response.text

    expected_count = len(
        [c for c in CATEGORIES if c["parent_name"] == parent_name]
    )
    if parent_name is None:
        # roots include the auto-seeded Einnahmen / Ausgaben
        expected_count += len(SEEDED_ROOTS)
    assert expected_count == len(response_data)


@pytest.mark.order(24)
def test_update_category(client):
    cat_id = _find_id(client, "Train")
    assert cat_id is not None

    patch_resp = client.patch(
        f"/api/categories/{cat_id}", json={"name": "Train Renamed"}
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["name"] == "Train Renamed"

    # Rename back so downstream tests keep working
    client.patch(f"/api/categories/{cat_id}", json={"name": "Train"})


@pytest.mark.order(25)
@pytest.mark.parametrize("root", SEEDED_ROOTS)
def test_seeded_root_cannot_be_modified(client, root):
    cat_id = _find_id(client, root)
    assert cat_id is not None

    patch_resp = client.patch(
        f"/api/categories/{cat_id}", json={"name": f"{root} (renamed)"}
    )
    assert patch_resp.status_code == 409

    del_resp = client.delete(f"/api/categories/{cat_id}")
    assert del_resp.status_code == 409


@pytest.mark.order(26)
def test_delete_cascades_to_subtree_and_rules(client):
    """Deleting a category should also delete its descendants and any rules
    pointing at the deleted categories. Self-contained: creates and deletes
    its own subtree, leaving the suite's other fixtures untouched."""
    ausgaben_id = _find_id(client, "Ausgaben")

    parent_id = client.post(
        "/api/categories/", json={"name": "CascadeRoot", "parent_id": ausgaben_id}
    ).json()["id"]
    child_id = client.post(
        "/api/categories/", json={"name": "CascadeChild", "parent_id": parent_id}
    ).json()["id"]
    grandchild_id = client.post(
        "/api/categories/", json={"name": "CascadeLeaf", "parent_id": child_id}
    ).json()["id"]

    rule_resp = client.post(
        "/api/rules/",
        json={"entity": "CascadeEntity", "category_name": "CascadeLeaf"},
    )
    assert rule_resp.status_code == 201, rule_resp.text
    rule_id = rule_resp.json()["id"]

    del_resp = client.delete(f"/api/categories/{parent_id}")
    assert del_resp.status_code == 204, del_resp.text

    # The entire subtree must be gone.
    for cid in (parent_id, child_id, grandchild_id):
        assert client.get(f"/api/categories/{cid}").status_code == 404

    # The rule that pointed at a deleted category must also be gone.
    rules = client.get("/api/rules/").json()
    assert not any(r["id"] == rule_id for r in rules), \
        f"rule {rule_id} should have been cascade-deleted, got: {rules}"
