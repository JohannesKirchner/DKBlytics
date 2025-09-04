from __future__ import annotations

from nicegui import ui

from .views import balance as balance_view
from .views import categorization as categorization_view
from .views import transactions as transactions_view


def _favicon() -> None:
    # simple emoji favicon so you can spot the tab easily
    ui.add_head_html(
        "<link rel='icon' href='data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><text y=\".9em\" font-size=\"90\">💶</text></svg>'>"
    )


@ui.page("/")
async def index_page() -> None:
    _favicon()
    await categorization_view.render()


@ui.page("/categorization")
async def categorization_page() -> None:
    _favicon()
    await categorization_view.render()


@ui.page("/transactions")
async def transactions_page() -> None:
    _favicon()
    await transactions_view.render()


@ui.page("/balance")
async def balance_page() -> None:
    _favicon()
    await balance_view.render()


def run() -> None:
    # Make it callable from other processes and avoid the main-guard pitfall on macOS spawn
    ui.run(title="DKBlytics UI")


# IMPORTANT for NiceGUI w/ multiprocessing (macOS, uv, etc.)
# See error hint: allow for __mp_main__ in addition to __main__
if __name__ in {"__main__", "__mp_main__"}:
    run()
