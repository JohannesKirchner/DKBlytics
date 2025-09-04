from __future__ import annotations

from nicegui import ui


def navbar(active_path: str) -> None:
    with ui.header().classes("items-center justify-between px-4"):  # top bar on each page
        ui.label("DKBlytics UI").classes("text-lg font-semibold")
        with ui.row().classes("gap-4"):
            def link(path: str, label: str) -> None:
                cls = "text-sm"
                if active_path == path:
                    cls += " underline font-bold"
                ui.link(label, path).classes(cls)

            link("/categorization", "Categorization")
            link("/transactions", "Transactions")
            link("/balance", "Balance")