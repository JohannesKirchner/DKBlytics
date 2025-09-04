from __future__ import annotations

from typing import Any, Dict

from nicegui import ui

from ..components.nav import navbar
from ..state import api


async def _refresh_connectivity(stats_labels: Dict[str, Any]) -> None:
    try:
        accounts = await api.get_accounts()
        categories = await api.get_categories()
        page = await api.get_transactions(limit=1, offset=0)
        stats_labels["acc"].text = f"Accounts: {len(accounts)}"
        stats_labels["cat"].text = f"Categories: {len(categories)}"
        stats_labels["tx"].text = f"Transactions: {page['total']}"
    except Exception as e:  # broad for first step; we’ll tighten later
        ui.notify(f"Connectivity error: {e}", color="negative")


async def _update_from_bank(output_md: Any, button: Any) -> None:
    button.disable()
    try:
        result = await api.update_from_bank()
        if isinstance(result, dict) and result:
            lines = [f"- **{k}**: {v}" for k, v in result.items()]
            output_md.set_content("\n".join(["### Inserted", *lines]))
        else:
            output_md.set_content("No new transactions.")
        ui.notify("Bank sync complete", color="positive")
    except Exception as e:
        ui.notify(f"Bank sync failed: {e}", color="negative")
    finally:
        button.enable()


async def render() -> None:
    navbar("/categorization")

    with ui.row().classes("w-full p-4 gap-4"):
        with ui.card().classes("w-full max-w-5xl"):  # Workbench container
            ui.label("Categorization").classes("text-2xl font-bold")

            # Actions row
            with ui.row().classes("items-center gap-3"):
                sync_btn = ui.button("Update from DKB")
                result_md = ui.markdown("")
                sync_btn.on_click(lambda: _update_from_bank(result_md, sync_btn))

            ui.separator()

            # Connectivity panel (quick sanity check)
            ui.label("Connectivity").classes("text-lg font-semibold")
            with ui.row().classes("gap-6"):
                acc = ui.label("Accounts: …")
                cat = ui.label("Categories: …")
                tx = ui.label("Transactions: …")
                stats = {"acc": acc, "cat": cat, "tx": tx}
                ui.button("Refresh", on_click=lambda: _refresh_connectivity(stats))
                ui.timer(0.1, lambda: _refresh_connectivity(stats), once=True)

            ui.separator()
            ui.markdown(
                """
                _Step 1 skeleton:_
                - Drag & drop assignment, rules editor, and category tree will land in Step 2.
                - For now, use the **Update from DKB** button and the **Connectivity** panel to verify wiring.
                """
            ).classes("text-sm text-gray-600")