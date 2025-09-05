# frontend/api/accounts.py
from typing import List, Dict, Any
from app.api.client import APIClient

client = APIClient()

def get_all_accounts() -> List[Dict[str, Any]]:
    """Get all accounts."""
    return client.get("/api/accounts/")

def get_account_by_id(public_id: str) -> Dict[str, Any]:
    """Get a specific account by public ID."""
    return client.get(f"/api/accounts/{public_id}")