# frontend/main.py
from nicegui import ui
from app.components.navigation import create_page_layout
from app.pages.transactions import render_transactions_page
from app.pages.categories import render_categories_page
from app.pages.balance import render_balance_page
from app.pages.budget import render_budget_page

@ui.page('/')
def home():
    with create_page_layout("Dashboard"):
        ui.label("Welcome to DKBlytics").classes('text-3xl font-bold mb-4')
        
        # Dashboard overview cards
        with ui.row().classes('gap-6 mb-6'):
            with ui.card().classes('p-6'):
                ui.label("Quick Actions").classes('text-xl mb-4')
                with ui.column().classes('gap-2'):
                    ui.button("Categorize Transactions", on_click=lambda: ui.navigate.to('/transactions')).props('color=primary')
                    ui.button("Manage Categories", on_click=lambda: ui.navigate.to('/categories')).props('outlined')
                    ui.button("View Balance", on_click=lambda: ui.navigate.to('/balance')).props('outlined')
                    ui.button("Budget Overview", on_click=lambda: ui.navigate.to('/budget')).props('outlined')
            
            with ui.card().classes('p-6'):
                ui.label("Getting Started").classes('text-xl mb-4')
                with ui.column().classes('gap-2'):
                    ui.label("1. Create your expense/income categories")
                    ui.label("2. Assign uncategorized transactions to categories")  
                    ui.label("3. Review your spending patterns and balance")
                    ui.label("4. Monitor your monthly/yearly budget")

@ui.page('/transactions')
def transactions():
    with create_page_layout("Transactions"):
        render_transactions_page()

@ui.page('/categories')
def categories():
    with create_page_layout("Categories"):
        render_categories_page()

@ui.page('/balance')
def balance():
    with create_page_layout("Balance"):
        render_balance_page()

@ui.page('/budget')
def budget():
    with create_page_layout("Budget"):
        render_budget_page()

def run() -> None:
    # Make it callable from other processes and avoid the main-guard pitfall on macOS spawn
    ui.run(port=8081, title="DKBlytics UI", reload=True)


# IMPORTANT for NiceGUI w/ multiprocessing (macOS, uv, etc.)
# See error hint: allow for __mp_main__ in addition to __main__
if __name__ in {"__main__", "__mp_main__"}:
    run()
