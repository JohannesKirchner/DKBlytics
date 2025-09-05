# app/pages/balance.py
from nicegui import ui
from app.api.transactions import get_transactions
from app.utils import create_loading_accounts_dropdown, create_date_inputs, safe_execute, create_error_message, create_empty_state
from app.constants import CSS_CLASSES, DEFAULTS
from datetime import datetime

def render_balance_page():
    """Render the balance overview page."""
    ui.label("Balance Overview").classes(CSS_CLASSES['page_title'])
    
    # Account selection and date range
    controls_container = ui.row().classes(CSS_CLASSES['control_row'])
    chart_container = ui.column().classes('w-full')
    
    with controls_container:
        # Account selection
        account_select = create_loading_accounts_dropdown("Account")
        
        # Date range (default from constants)
        date_from, date_to = create_date_inputs(DEFAULTS['balance_history_days'])
        
        # Load data button
        ui.button("Update Chart", on_click=lambda: load_balance_data()).props('color=primary')
    
    
    def load_balance_data():
        """Load and display balance evolution chart."""
        chart_container.clear()
        
        try:
            # Get transactions for the selected period
            account_id = account_select.value if account_select.value != "all" else None
            
            transactions = get_transactions(
                limit=1000,  # Get many transactions for balance calculation
                date_from=date_from.value,
                date_to=date_to.value,
                account_id=account_id,
                sort_by="date_asc"  # Sort by date ascending
            )
            
            if not transactions.get("items"):
                create_empty_state(chart_container, "No transactions found for the selected period")
                return
            
            # Calculate running balance
            balance_data = []
            running_balance = 0
            
            # Get starting balance (simplified - assumes 0 start)
            for tx in transactions["items"]:
                running_balance += tx["amount"]
                balance_data.append({
                    "date": tx["date"],
                    "balance": running_balance,
                    "amount": tx["amount"]
                })
            
            # Create chart data
            chart_data = {
                "chart": {
                    "type": "line",
                    "height": DEFAULTS['chart_height']
                },
                "title": {
                    "text": "Balance Evolution"
                },
                "xAxis": {
                    "type": "datetime",
                    "title": {"text": "Date"}
                },
                "yAxis": {
                    "title": {"text": "Balance (€)"}
                },
                "series": [{
                    "name": "Balance",
                    "data": [[datetime.strptime(item["date"], "%Y-%m-%d").timestamp() * 1000, item["balance"]] for item in balance_data]
                }],
                "tooltip": {
                    "valueDecimals": 2,
                    "valueSuffix": "€"
                }
            }
            
            with chart_container:
                ui.highchart(chart_data).classes('w-full h-96')
                
                # Summary stats
                with ui.card().classes('mt-4'):
                    ui.label("Summary").classes(CSS_CLASSES['card_title'])
                    with ui.grid(columns=3).classes('gap-4'):
                        ui.label(f"Starting Balance: {balance_data[0]['balance'] - balance_data[0]['amount']:.2f}€")
                        ui.label(f"Ending Balance: {balance_data[-1]['balance']:.2f}€")
                        ui.label(f"Net Change: {balance_data[-1]['balance'] - (balance_data[0]['balance'] - balance_data[0]['amount']):.2f}€")
                        
        except Exception as e:
            create_error_message(chart_container, f"Error loading balance data: {str(e)}")
    
    # Initialize
    load_balance_data()