# frontend/api/transactions.py
from typing import List, Dict, Any, Optional
from app.api.client import APIClient

client = APIClient()

def get_uncategorized_transactions(limit=50, offset=0):
    return client.get("/api/transactions/", params={
        "category": "null",
        "limit": limit,
        "offset": offset,
    })

def get_transactions(
    limit: int = 50,
    offset: int = 0,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "date_desc"
) -> Dict[str, Any]:
    """Get transactions with filters."""
    params = {
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
    }
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if account_id:
        params["account_id"] = account_id
    if category:
        params["category"] = category
    
    return client.get("/api/transactions/", params=params)

def get_transaction_summary(
    scope_name: Optional[str] = None,
    depth: int = 1,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get transaction summary by category."""
    params = {
        "depth": depth,
    }
    if scope_name:
        params["scope_name"] = scope_name
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if account_id:
        params["account_id"] = account_id
    
    return client.get("/api/transactions/summary", params=params)
