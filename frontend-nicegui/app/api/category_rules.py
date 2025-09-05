# frontend/api/category_rules.py
from typing import List, Dict, Any
from app.api.client import APIClient

client = APIClient()

def get_all_category_rules() -> List[Dict[str, Any]]:
    """Get all category rules."""
    return client.get("/api/rules/")

def create_category_rule(entity: str, text: str, category_name: str) -> Dict[str, Any]:
    """Create a category rule."""
    return client.post("/api/rules/", data={
        "entity": entity,
        "text": text,
        "category_name": category_name,
    })

def delete_category_rule(rule_id: int) -> int:
    """Delete a category rule by ID."""
    return client.delete(f"/api/rules/{rule_id}")