# app/pages/balance.py
from nicegui import ui
from app.api.transactions import get_transactions
from app.api.accounts import get_all_accounts, get_account_by_id
from app.utils import create_loading_accounts_dropdown, create_date_inputs, safe_execute, create_error_message, create_empty_state
from app.constants import CSS_CLASSES, DEFAULTS
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any
import math


def render_balance_page():
    """Render the enhanced balance overview page."""
    ui.label("Balance Overview").classes(CSS_CLASSES['page_title'])
    
    # Controls container
    controls_container = ui.column().classes('mb-4')
    
    # Main content containers
    summary_container = ui.row().classes('gap-4 mb-6')
    charts_container = ui.column().classes('w-full')
    
    # Filter state
    current_filters = {
        'account_id': 'all',
        'date_from': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
        'date_to': datetime.now().strftime('%Y-%m-%d'),
    }
    
    def load_balance_data():
        """Load and display enhanced balance data."""
        summary_container.clear()
        charts_container.clear()
        
        try:
            # Get account data
            if current_filters['account_id'] == 'all' or not current_filters['account_id']:
                accounts = get_all_accounts()
                selected_accounts = accounts
            else:
                account = get_account_by_id(current_filters['account_id'])
                selected_accounts = [account]
                accounts = get_all_accounts()  # Still need all for totals
            
            # Get transactions for the period
            transactions_response = get_transactions(
                limit=500,  # Maximum allowed by API
                date_from=current_filters['date_from'],
                date_to=current_filters['date_to'],
                account_id=current_filters['account_id'] if current_filters['account_id'] and current_filters['account_id'] != 'all' else None,
                sort_by="date_desc"  # Most recent first
            )
            
            transactions = transactions_response.get("items", [])
            
            # Create summary cards
            create_balance_summary(summary_container, selected_accounts, accounts, transactions)
            
            # Create charts
            with charts_container:
                # Balance evolution chart
                create_balance_evolution_chart(selected_accounts, transactions, current_filters)
                
                ui.separator().classes('my-6')
                
                # Income vs Expenses chart
                create_income_expenses_chart(transactions, current_filters)
                
                if current_filters['account_id'] == 'all' and len(accounts) > 1:
                    ui.separator().classes('my-6')
                    # Multi-account balance chart
                    create_multi_account_chart(accounts, current_filters)
        
        except Exception as e:
            create_error_message(charts_container, f"Error loading balance data: {str(e)}")
    
    # Create filter controls
    create_balance_filters(controls_container, current_filters, load_balance_data)
    
    # Initial load
    load_balance_data()


def create_balance_filters(container, filters: Dict, reload_callback):
    """Create filter controls for balance page."""
    with container:
        ui.label("Filters").classes(CSS_CLASSES['card_title'])
        
        with ui.card().classes('p-4'):
            with ui.row().classes('gap-4 items-end'):
                # Account selection
                account_select = create_loading_accounts_dropdown("Account")
                account_select.value = 'all'  # Ensure default value is set
                account_select.bind_value(filters, 'account_id')
                
                # Date range
                date_from = ui.input("From Date").props('type=date outlined')
                date_from.bind_value(filters, 'date_from')
                
                date_to = ui.input("To Date").props('type=date outlined') 
                date_to.bind_value(filters, 'date_to')
                
                # Quick date buttons
                with ui.column().classes('gap-1'):
                    ui.label("Quick Select").classes('text-sm text-gray-600')
                    with ui.row().classes('gap-1'):
                        def set_last_30_days():
                            filters['date_from'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                            filters['date_to'] = datetime.now().strftime('%Y-%m-%d')
                            reload_callback()
                        
                        def set_last_90_days():
                            filters['date_from'] = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                            filters['date_to'] = datetime.now().strftime('%Y-%m-%d')
                            reload_callback()
                        
                        def set_last_year():
                            filters['date_from'] = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                            filters['date_to'] = datetime.now().strftime('%Y-%m-%d')
                            reload_callback()
                        
                        ui.button("30d", on_click=set_last_30_days).props('size=sm outline')
                        ui.button("90d", on_click=set_last_90_days).props('size=sm outline')
                        ui.button("1y", on_click=set_last_year).props('size=sm outline')
                
                # Update button
                ui.button("Update", on_click=reload_callback, icon="refresh").props('color=primary')


def create_balance_summary(container, selected_accounts: List[Dict], all_accounts: List[Dict], transactions: List[Dict]):
    """Create summary cards showing key balance metrics."""
    with container:
        # Calculate totals
        current_balance = sum(float(acc.get('balance', 0)) for acc in selected_accounts)
        total_balance = sum(float(acc.get('balance', 0)) for acc in all_accounts)
        
        # Calculate period changes
        total_income = sum(float(tx['amount']) for tx in transactions if float(tx['amount']) > 0)
        total_expenses = sum(abs(float(tx['amount'])) for tx in transactions if float(tx['amount']) < 0)
        net_change = total_income - total_expenses
        
        # Current Balance Card
        with ui.card().classes('p-4 bg-blue-50'):
            ui.label("Current Balance").classes('text-sm text-gray-600')
            ui.label(f"€{current_balance:,.2f}").classes('text-2xl font-bold text-blue-700')
            if len(selected_accounts) < len(all_accounts):
                ui.label(f"of €{total_balance:,.2f} total").classes('text-xs text-gray-500')
        
        # Period Income Card
        with ui.card().classes('p-4 bg-green-50'):
            ui.label("Period Income").classes('text-sm text-gray-600')
            ui.label(f"€{total_income:,.2f}").classes('text-2xl font-bold text-green-700')
            ui.label(f"From {len([tx for tx in transactions if float(tx['amount']) > 0])} transactions").classes('text-xs text-gray-500')
        
        # Period Expenses Card  
        with ui.card().classes('p-4 bg-red-50'):
            ui.label("Period Expenses").classes('text-sm text-gray-600')
            ui.label(f"€{total_expenses:,.2f}").classes('text-2xl font-bold text-red-700')
            ui.label(f"From {len([tx for tx in transactions if float(tx['amount']) < 0])} transactions").classes('text-xs text-gray-500')
        
        # Net Change Card
        color = 'green' if net_change >= 0 else 'red'
        with ui.card().classes(f'p-4 bg-{color}-50'):
            ui.label("Net Change").classes('text-sm text-gray-600')
            sign = '+' if net_change >= 0 else ''
            ui.label(f"{sign}€{net_change:,.2f}").classes(f'text-2xl font-bold text-{color}-700')
            ui.label("This period").classes('text-xs text-gray-500')


def create_balance_evolution_chart(accounts: List[Dict], transactions: List[Dict], filters: Dict):
    """Create balance evolution chart with proper balance calculation."""
    ui.label("Balance Evolution").classes(CSS_CLASSES['section_title'])
    
    if not transactions:
        create_empty_state(ui.column(), "No transactions found for the selected period")
        return
    
    # Get current balance for selected accounts
    current_total_balance = sum(float(acc.get('balance', 0)) for acc in accounts)
    
    # Sort transactions by date (oldest first for balance calculation)
    sorted_transactions = sorted(transactions, key=lambda x: x['date'])
    
    # Calculate historical balance by working backwards from current balance
    balance_data = []
    running_balance = current_total_balance
    
    # First, subtract all future transactions (after the period) to get end-of-period balance
    future_transactions_response = get_transactions(
        limit=500,
        date_from=filters['date_to'],
        account_id=filters['account_id'] if filters['account_id'] and filters['account_id'] != 'all' else None,
        sort_by="date_asc"
    )
    
    future_transactions = future_transactions_response.get("items", [])
    for tx in future_transactions:
        if tx['date'] > filters['date_to']:  # Only future transactions
            running_balance -= float(tx['amount'])
    
    # Now work backwards through the period transactions
    for tx in reversed(sorted_transactions):
        balance_data.append({
            "date": tx["date"],
            "balance": running_balance
        })
        running_balance -= float(tx['amount'])
    
    # Reverse to get chronological order and add starting point
    balance_data.reverse()
    if balance_data:
        # Add starting balance point
        start_date = sorted_transactions[0]['date']
        balance_data.insert(0, {
            "date": start_date,
            "balance": running_balance + float(sorted_transactions[0]['amount'])
        })
    
    # Create chart
    chart_data = {
        "chart": {"type": "line", "height": 400},
        "title": {"text": "Balance Evolution Over Time"},
        "xAxis": {
            "type": "datetime",
            "title": {"text": "Date"}
        },
        "yAxis": {"title": {"text": "Balance (€)"}},
        "series": [{
            "name": "Balance",
            "data": [[datetime.strptime(item["date"], "%Y-%m-%d").timestamp() * 1000, item["balance"]] for item in balance_data],
            "color": "#2563eb"
        }],
        "tooltip": {
            "valueDecimals": 2,
            "valueSuffix": "€"
        }
    }
    
    ui.highchart(chart_data).classes('w-full')


def create_income_expenses_chart(transactions: List[Dict], filters: Dict):
    """Create income vs expenses chart."""
    ui.label("Income vs Expenses").classes(CSS_CLASSES['section_title'])
    
    if not transactions:
        create_empty_state(ui.column(), "No transactions found for the selected period")
        return
    
    # Group transactions by month
    monthly_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
    
    for tx in transactions:
        date = datetime.strptime(tx['date'], '%Y-%m-%d')
        month_key = date.strftime('%Y-%m')
        amount = float(tx['amount'])
        
        if amount > 0:
            monthly_data[month_key]['income'] += amount
        else:
            monthly_data[month_key]['expenses'] += abs(amount)
    
    # Sort by month
    sorted_months = sorted(monthly_data.keys())
    
    # Prepare chart data
    categories = [datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in sorted_months]
    income_data = [monthly_data[month]['income'] for month in sorted_months]
    expenses_data = [monthly_data[month]['expenses'] for month in sorted_months]
    
    chart_data = {
        "chart": {"type": "column", "height": 400},
        "title": {"text": "Monthly Income vs Expenses"},
        "xAxis": {"categories": categories},
        "yAxis": {"title": {"text": "Amount (€)"}},
        "series": [
            {
                "name": "Income",
                "data": income_data,
                "color": "#10b981"
            },
            {
                "name": "Expenses", 
                "data": expenses_data,
                "color": "#ef4444"
            }
        ],
        "tooltip": {
            "valueDecimals": 2,
            "valueSuffix": "€"
        }
    }
    
    ui.highchart(chart_data).classes('w-full')


def create_multi_account_chart(accounts: List[Dict], filters: Dict):
    """Create multi-line chart showing balance evolution for each account."""
    ui.label("Balance by Account").classes(CSS_CLASSES['section_title'])
    
    series_data = []
    colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
    
    for i, account in enumerate(accounts):
        # Get transactions for this specific account
        account_transactions = get_transactions(
            limit=500,
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            account_id=account['public_id'],
            sort_by="date_asc"
        )
        
        transactions = account_transactions.get("items", [])
        if not transactions:
            continue
            
        # Calculate balance evolution for this account
        current_balance = float(account.get('balance', 0))
        balance_data = []
        running_balance = current_balance
        
        # Work backwards from current balance
        for tx in reversed(transactions):
            balance_data.append([
                datetime.strptime(tx["date"], "%Y-%m-%d").timestamp() * 1000,
                running_balance
            ])
            running_balance -= float(tx['amount'])
        
        balance_data.reverse()
        
        series_data.append({
            "name": account['name'],
            "data": balance_data,
            "color": colors[i % len(colors)]
        })
    
    if not series_data:
        create_empty_state(ui.column(), "No account data found for the selected period")
        return
    
    chart_data = {
        "chart": {"type": "line", "height": 400},
        "title": {"text": "Balance Evolution by Account"},
        "xAxis": {
            "type": "datetime",
            "title": {"text": "Date"}
        },
        "yAxis": {"title": {"text": "Balance (€)"}},
        "series": series_data,
        "tooltip": {
            "valueDecimals": 2,
            "valueSuffix": "€"
        }
    }
    
    ui.highchart(chart_data).classes('w-full')