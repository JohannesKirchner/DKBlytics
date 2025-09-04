from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

BASE_URL = os.getenv("DKBLYTICS_API_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(RuntimeError):
    pass


class ApiClient:
    """Thin async client around your FastAPI endpoints."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 15.0) -> None:
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    # --- Accounts ---
    async def get_accounts(self, *, name: Optional[str] = None, holder: Optional[str] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if holder is not None:
            params["holder"] = holder
        r = await self._client.get("/api/accounts/", params=params)
        r.raise_for_status()
        return r.json()

    # --- Categories ---
    async def get_categories(self) -> List[Dict[str, Any]]:
        r = await self._client.get("/api/categories/")
        r.raise_for_status()
        return r.json()

    async def create_category(self, *, name: str, parent_name: Optional[str] = None) -> Dict[str, Any]:
        payload = {"name": name, "parent_name": parent_name}
        r = await self._client.post("/api/categories/", json=payload)
        r.raise_for_status()
        return r.json()

    async def delete_category(self, *, name: str) -> None:
        # You said this endpoint exists now.
        r = await self._client.delete(f"/api/categories/{name}")
        if r.status_code not in (200, 204):
            r.raise_for_status()

    # --- Rules ---
    async def get_rules(self) -> List[Dict[str, Any]]:
        r = await self._client.get("/api/rules/")
        r.raise_for_status()
        return r.json()

    async def create_rule(self, *, entity: str, category_name: str, text: Optional[str] = None) -> Dict[str, Any]:
        payload = {"entity": entity, "category_name": category_name, "text": text}
        r = await self._client.post("/api/rules/", json=payload)
        r.raise_for_status()
        return r.json()

    async def delete_rule(self, *, rule_id: int) -> None:
        r = await self._client.delete(f"/api/rules/{rule_id}")
        if r.status_code not in (200, 204):
            r.raise_for_status()

    async def resolve_rule(self, *, entity: str, text: Optional[str] = None) -> Optional[str]:
        params = {"entity": entity, "text": text}
        r = await self._client.get("/api/rules/resolve", params=params)
        r.raise_for_status()
        return r.json()

    # --- Transactions ---
    async def get_transactions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "date_desc",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        account_id: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
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
        if q:
            params["q"] = q
        r = await self._client.get("/api/transactions/", params=params)
        r.raise_for_status()
        return r.json()

    async def summarize_transactions_by_category(
        self,
        *,
        scope_name: Optional[str] = None,
        depth: int = 1,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        account_id: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"depth": depth}
        if scope_name is not None:
            params["scope_name"] = scope_name
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if account_id:
            params["account_id"] = account_id
        if q:
            params["q"] = q
        r = await self._client.get("/api/transactions/summary", params=params)
        r.raise_for_status()
        return r.json()

    # --- Bank integration ---
    async def update_from_bank(self) -> Dict[str, Any]:
        r = await self._client.post("/api/bank/update_from_bank")
        r.raise_for_status()
        return r.json()
    