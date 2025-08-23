from typing import List, Optional, Dict
from ..database import get_db_connection
from ..models import (
    Category,
    CategoryRule,
)


def create_category_db(name: str, parent_id: Optional[int]) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories(name, parent_id) VALUES (?, ?);",
            (name, parent_id),
        )
        conn.commit()

        return cursor.fetchone()


def get_all_categories_db() -> List[Category]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, parent_id FROM categories;")
        rows = cursor.fetchall()

        return [Category(**dict(row)) for row in rows]


def build_category_tree(nodes: List[Category]) -> List[Dict]:
    # Build a nested tree in Python for the GET /categories/tree endpoint
    by_id = {n.id: {"id": n.id, "name": n.name, "children": []} for n in nodes}
    roots: List[Dict] = []
    for n in nodes:
        node = by_id[n.id]
        if n.parent_id and n.parent_id in by_id:
            by_id[n.parent_id]["children"].append(node)
        else:
            roots.append(node)

    # stable sort children by name
    def sort_subtree(sub):
        sub["children"].sort(key=lambda x: x["name"].lower())
        for ch in sub["children"]:
            sort_subtree(ch)

    for r in roots:
        sort_subtree(r)
    return roots


def get_category_rule_db(text: str, entity: str) -> Optional[CategoryRule]:
    """Retrieves a category by text and entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM category_rules WHERE text = ? AND entity = ?", (text, entity)
        )
        return cursor.fetchone()


def create_category_rule_if_not_exists(text: str, entity: str) -> None:
    """
    Adds a new category rule with a null category if it doesn't already exist.
    Existing category rules are not touched.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO category_rules (text, entity, category_id) VALUES (?, ?, NULL)",
            (text, entity),
        )
        conn.commit()


def get_all_category_rules_db(
    text: Optional[str] = None, entity: Optional[str] = None
) -> List[CategoryRule]:
    """Retrieves all category rules."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT * FROM category_rules WHERE 1=1
        """
        params = []

        if text:
            query += " AND text LIKE ?"
            params.append(f"%{text}%")
        if entity:
            query += " AND entity LIKE ?"
            params.append(f"%{entity}%")

        cursor.execute(query, params)
        return cursor.fetchall()


def update_category_rule_by_text_and_entity_db(
    text: str, entity: str, category_id: int
) -> bool:
    """Updates a specific category rule by text and entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE category_rules SET category_id = ? WHERE text = ? AND entity = ?",
            (category_id, text, entity),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_category_rule_by_entity_db(entity: str, category_id: int) -> int:
    """Updates the category for all rules matching a given entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE category_rules SET category_id = ? WHERE entity = ?",
            (category_id, entity),
        )
        conn.commit()
        return cursor.rowcount
