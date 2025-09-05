# app/pages/budget.py
from nicegui import ui
from app.api.transactions import get_transaction_summary
from app.utils import create_loading_accounts_dropdown, create_error_message, create_empty_state, create_summary_cards
from app.constants import CHART_COLORS, CSS_CLASSES
from datetime import datetime
import calendar

def render_budget_page():
    """Render the budget overview page."""
    ui.label("Monthly/Yearly Budget").classes(CSS_CLASSES['page_title'])
    
    # Controls
    controls_container = ui.row().classes(CSS_CLASSES['control_row'])
    content_container = ui.column().classes('w-full')
    
    with controls_container:
        # Period selection
        period_select = ui.select(
            options=[
                {"label": "Monthly", "value": "monthly"},
                {"label": "Yearly", "value": "yearly"}
            ],
            label="Period",
            value="monthly"
        ).props('outlined')
        
        # Year selection
        current_year = datetime.now().year
        year_select = ui.select(
            options=[{"label": str(year), "value": year} for year in range(current_year-2, current_year+2)],
            label="Year",
            value=current_year
        ).props('outlined')
        
        # Month selection (only for monthly view)
        month_select = ui.select(
            options=[{"label": calendar.month_name[i], "value": i} for i in range(1, 13)],
            label="Month",
            value=datetime.now().month
        ).props('outlined')
        
        # Account selection
        account_select = create_loading_accounts_dropdown("Account")
        
        # Update button
        ui.button("Update View", on_click=lambda: load_budget_data()).props('color=primary')
    
    # Show/hide month selector based on period
    def on_period_change():
        month_select.visible = period_select.value == "monthly"
    
    period_select.on_value_change(on_period_change)
    on_period_change()  # Set initial state
    
    
    def load_budget_data():
        """Load and display budget data."""
        content_container.clear()
        
        try:
            # Calculate date range based on period
            if period_select.value == "monthly":
                year = year_select.value
                month = month_select.value
                date_from = f"{year}-{month:02d}-01"
                
                # Get last day of month
                _, last_day = calendar.monthrange(year, month)
                date_to = f"{year}-{month:02d}-{last_day:02d}"
                
                period_label = f"{calendar.month_name[month]} {year}"
            else:  # yearly
                year = year_select.value
                date_from = f"{year}-01-01"
                date_to = f"{year}-12-31"
                period_label = str(year)
            
            # Get account filter
            account_id = account_select.value if account_select.value != "all" else None
            
            # Get transaction summary
            summary = get_transaction_summary(
                date_from=date_from,
                date_to=date_to,
                account_id=account_id,
                depth=1  # Top-level categories
            )
            
            with content_container:
                ui.label(f"Budget Overview - {period_label}").classes(CSS_CLASSES['section_title'])
                
                if not summary:
                    create_empty_state(content_container, "No transactions found for the selected period")
                    return
                
                # Separate income and expenses
                income_items = [item for item in summary if item["total_amount"] > 0]
                expense_items = [item for item in summary if item["total_amount"] < 0]
                
                # Calculate totals
                total_income = sum(item["total_amount"] for item in income_items)
                total_expenses = sum(abs(item["total_amount"]) for item in expense_items)
                net_amount = total_income - total_expenses
                
                # Summary cards
                create_summary_cards([
                    {
                        'label': 'Total Income',
                        'value': f"{total_income:.2f}€",
                        'label_classes': 'text-green-600 font-bold'
                    },
                    {
                        'label': 'Total Expenses', 
                        'value': f"{total_expenses:.2f}€",
                        'label_classes': 'text-red-600 font-bold'
                    },
                    {
                        'label': 'Net Amount',
                        'value': f"{net_amount:.2f}€", 
                        'label_classes': 'text-blue-600 font-bold'
                    }
                ])
                
                # Charts container
                with ui.row().classes('gap-6 w-full'):
                    # Income chart
                    if income_items:
                        with ui.column().classes('flex-1'):
                            ui.label("Income by Category").classes(CSS_CLASSES['card_title'])
                            income_chart = create_pie_chart(income_items, "Income", "green")
                            ui.highchart(income_chart).classes('h-80')
                    
                    # Expenses chart
                    if expense_items:
                        with ui.column().classes('flex-1'):
                            ui.label("Expenses by Category").classes(CSS_CLASSES['card_title'])
                            # Convert to positive values for chart
                            expense_items_positive = [{**item, "total_amount": abs(item["total_amount"])} for item in expense_items]
                            expense_chart = create_pie_chart(expense_items_positive, "Expenses", "red")
                            ui.highchart(expense_chart).classes('h-80')
                
                # Detailed breakdown table
                with ui.card().classes('mt-6'):
                    ui.label("Detailed Breakdown").classes(CSS_CLASSES['card_title'])
                    
                    # Combine all items for table
                    all_items = []
                    for item in income_items:
                        all_items.append({
                            "category": item["category_name"] or "Uncategorized",
                            "type": "Income",
                            "amount": item["total_amount"],
                            "count": item["transaction_count"]
                        })
                    
                    for item in expense_items:
                        all_items.append({
                            "category": item["category_name"] or "Uncategorized", 
                            "type": "Expense",
                            "amount": item["total_amount"],
                            "count": item["transaction_count"]
                        })
                    
                    if all_items:
                        # Format amounts in the data instead of using lambda
                        for item in all_items:
                            item['formatted_amount'] = f"{item['amount']:.2f}"
                        
                        ui.table(
                            columns=[
                                {'name': 'category', 'label': 'Category', 'field': 'category'},
                                {'name': 'type', 'label': 'Type', 'field': 'type'},
                                {'name': 'formatted_amount', 'label': 'Amount (€)', 'field': 'formatted_amount'},
                                {'name': 'count', 'label': 'Transactions', 'field': 'count'},
                            ],
                            rows=all_items,
                            row_key='category'
                        ).classes('w-full')
                        
        except Exception as e:
            create_error_message(content_container, f"Error loading budget data: {str(e)}")

def create_pie_chart(data, title_suffix, color_scheme):
    """Create a pie chart for category data."""
    chart_data = []
    colors = []
    
    base_colors = CHART_COLORS.get(color_scheme, CHART_COLORS['blue'])
    
    for i, item in enumerate(data):
        chart_data.append({
            "name": item["category_name"] or "Uncategorized",
            "y": item["total_amount"],
            "color": base_colors[i % len(base_colors)]
        })
    
    return {
        "chart": {"type": "pie", "height": 300},
        "title": {"text": title_suffix},
        "series": [{
            "name": "Amount",
            "data": chart_data
        }],
        "tooltip": {
            "valueDecimals": 2,
            "valueSuffix": "€"
        },
        "plotOptions": {
            "pie": {
                "dataLabels": {
                    "enabled": True,
                    "format": "{point.name}: {point.percentage:.1f}%"
                }
            }
        }
    }

