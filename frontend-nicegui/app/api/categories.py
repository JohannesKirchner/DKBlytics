# frontend/api/categories.py
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from app.api.client import APIClient

client = APIClient()

def get_all_categories() -> List[Dict[str, Any]]:
    """Get all categories as a flat list."""
    return client.get("/api/categories/")

def get_category_tree(parent_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get categories as a nested tree structure."""
    params = {}
    if parent_name:
        params["name"] = parent_name
    return client.get("/api/categories/tree", params=params)

def create_category(name: str, parent_name: Optional[str] = None) -> Dict[str, Any]:
    """Create a new category."""
    payload = {"name": name}
    if parent_name:
        payload["parent_name"] = parent_name
    return client.post("/api/categories/", data=payload)

def delete_category(name: str) -> int:
    """Delete a category by name."""
    # Ensure name is a string and properly encode for URL
    category_name = str(name) if name is not None else ""
    return client.delete(f"/api/categories/{quote(category_name, safe='')}")