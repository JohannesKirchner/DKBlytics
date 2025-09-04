from __future__ import annotations

from nicegui import app as nice_app

from .api import ApiClient

api = ApiClient()


@nice_app.on_shutdown
async def _close_api() -> None:
    # ensure HTTP client is closed on app shutdown
    await api.close()