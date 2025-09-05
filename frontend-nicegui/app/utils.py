# app/utils.py
"""Common utilities and helpers for the frontend."""

from nicegui import ui
from typing import Dict, List, Any, Callable, Optional
from app.api.accounts import get_all_accounts


def create_error_message(container, message: str):
    """Create a standardized error message in a container."""
    with container:
        ui.label(message).classes('text-red-500')


def create_empty_state(container, message: str):
    """Create a standardized empty state in a container."""
    with container:
        ui.label(message).classes('text-gray-500')


def create_loading_accounts_dropdown(label: str = "Account") -> ui.select:
    """Create an account dropdown and load accounts into it."""
    dropdown = ui.select([], label=label).props('outlined')
    
    def load_accounts():
        try:
            accounts = get_all_accounts()
            account_options = []
            for acc in accounts:
                # Safely convert balance to float
                balance = acc['balance']
                if isinstance(balance, str):
                    try:
                        balance = float(balance)
                    except ValueError:
                        balance = 0.0
                
                account_options.append({
                    "label": f"{acc['name']} ({balance:.2f}€)", 
                    "value": acc['public_id']
                })
            account_options.insert(0, {"label": "All Accounts", "value": "all"})
            
            dropdown.options = account_options
            dropdown.value = "all"
            
        except Exception as e:
            ui.notify(f"Error loading accounts: {str(e)}", color="negative")
    
    load_accounts()
    return dropdown


def create_date_inputs(default_days_back: int = 90):
    """Create standardized date input controls with defaults."""
    from datetime import datetime, timedelta
    
    today = datetime.now()
    start_date = today - timedelta(days=default_days_back)
    
    date_from = ui.input("From Date").props('type=date outlined')
    date_to = ui.input("To Date").props('type=date outlined')
    
    date_from.value = start_date.strftime("%Y-%m-%d")
    date_to.value = today.strftime("%Y-%m-%d")
    
    return date_from, date_to


def safe_execute(func: Callable, error_message: str, container=None):
    """Safely execute a function and handle errors."""
    try:
        return func()
    except Exception as e:
        error_msg = f"{error_message}: {str(e)}"
        if container:
            create_error_message(container, error_msg)
        else:
            ui.notify(error_msg, color="negative")
        return None


def format_currency(amount: float) -> str:
    """Format a number as currency."""
    return f"{amount:.2f}€"


def create_summary_cards(data: List[Dict[str, Any]], classes: str = "gap-4 mb-6"):
    """Create a row of summary cards."""
    with ui.row().classes(classes):
        for card_data in data:
            with ui.card():
                ui.label(card_data['label']).classes(card_data.get('label_classes', 'font-bold'))
                ui.label(card_data['value']).classes(card_data.get('value_classes', 'text-2xl'))


def create_delete_table_action(rows: List[Dict], delete_func: Callable, key_field: str = 'name'):
    """Create standardized table with delete actions."""
    def create_delete_handler(item_key):
        def delete_item(e):
            item_id = e.args if hasattr(e, 'args') else str(e) 
            try:
                delete_func(item_id)
                ui.notify(f"Item deleted successfully", color="positive")
            except Exception as e:
                ui.notify(f"Error deleting item: {str(e)}", color="negative")
        return delete_item
    
    # Add delete handlers to each row
    for row in rows:
        row['delete_handler'] = create_delete_handler(row[key_field])