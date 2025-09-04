from __future__ import annotations

from typing import Any, Dict

from nicegui import ui

from ..components.nav import navbar


async def render() -> None:
    navbar("/transactions")

    with ui.row().classes("w-full p-4 gap-4"):
        with ui.card().classes("w-full max-w-5xl"):
            ui.label("Transactions").classes("text-2xl font-bold")
            ui.markdown(
                """
                _Step 1 skeleton:_ filters, stacked category bars, and sidebar will arrive in Step 3.
                For now, this is a placeholder page so routing and layout are verified.
                """
            )