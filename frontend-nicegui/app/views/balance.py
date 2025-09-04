from __future__ import annotations

from nicegui import ui

from ..components.nav import navbar


async def render() -> None:
    navbar("/balance")

    with ui.row().classes("w-full p-4 gap-4"):
        with ui.card().classes("w-full max-w-5xl"):
            ui.label("Balance").classes("text-2xl font-bold")
            ui.markdown(
                """
                _Step 1 skeleton:_ reconstructed balance series and line chart will arrive in Step 4.
                This placeholder ensures navigation works.
                """
            )