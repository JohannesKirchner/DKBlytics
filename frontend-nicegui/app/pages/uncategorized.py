# app/pages/uncategorized.py
from nicegui import ui
from app.api.transactions import get_uncategorized_transactions
from app.api.category_rules import create_category_rule
from app.components.category_dropdown import category_dropdown
from app.utils import create_empty_state, format_currency
from app.constants import CSS_CLASSES, DEFAULTS

def render_uncategorized_page():
    ui.label("Uncategorized Transactions").classes(CSS_CLASSES['page_title'])

    table_container = ui.column()

    def load_transactions():
        table_container.clear()

        data = get_uncategorized_transactions(limit=DEFAULTS['transactions_limit'])
        transactions = data.get("items", [])

        if not transactions:
            create_empty_state(table_container, "No uncategorized transactions found.")
            return
        
        with table_container:

            # Build table rows
            rows = [
                {
                    "id": tx["id"],
                    "date": tx["date"],
                    "entity": tx["entity"],
                    "text": tx["text"],
                    "amount": tx["amount"],
                    "transaction": tx  # Keep full transaction for later use
                }
                for tx in transactions
            ]

            # Format amount values in the rows
            for row in rows:
                # Ensure amount is a number before formatting
                amount = row['amount']
                if isinstance(amount, str):
                    try:
                        amount = float(amount)
                    except ValueError:
                        amount = 0.0
                row['amount'] = format_currency(amount)
            
            # Create table with selection
            table = ui.table(
                columns=[
                    {'name': 'date', 'label': 'Date', 'field': 'date'},
                    {'name': 'entity', 'label': 'Entity', 'field': 'entity'},
                    {'name': 'text', 'label': 'Text', 'field': 'text'},
                    {'name': 'amount', 'label': 'Amount', 'field': 'amount'},
                ],
                rows=rows,
                row_key='id',
                selection='multiple'
            )

            # Add assignment controls below the table
            ui.label("Assign Categories").classes(CSS_CLASSES['section_title'] + ' mt-6')
            
            with ui.row().classes('gap-4 items-end mb-4'):
                selected_dropdown = category_dropdown(label="Select Category")
                
                def assign_to_selected():
                    if not table.selected:
                        ui.notify("Please select transactions first", color="negative") 
                        return
                    if not selected_dropdown.value:
                        ui.notify("Please select a category", color="negative")
                        return
                    
                    try:
                        # Assign to all selected transactions
                        for selected_row in table.selected:
                            tx = selected_row['transaction']
                            create_category_rule(
                                entity=tx['entity'],
                                text=tx['text'],
                                category_name=selected_dropdown.value
                            )
                        
                        ui.notify(f"Assigned {len(table.selected)} transactions to {selected_dropdown.value}")
                        load_transactions()
                    except Exception as e:
                        ui.notify(f"Error creating rules: {str(e)}", color="negative")
                
                ui.button("Assign Selected", on_click=assign_to_selected).props('color=primary')
                ui.label(f"Select transactions by clicking the checkboxes").classes('text-sm text-gray-600')


    load_transactions()
    ui.button("Refresh", on_click=load_transactions).classes('mt-4')
