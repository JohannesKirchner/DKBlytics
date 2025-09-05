# app/pages/uncategorized.py
from nicegui import ui
from app.api.transactions import get_uncategorized_transactions
from app.api.category_rules import create_category_rule, create_entity_only_rule, apply_rules_to_transactions
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
                
                def assign_exact_rules():
                    if not table.selected:
                        ui.notify("Please select transactions first", color="negative") 
                        return
                    if not selected_dropdown.value:
                        ui.notify("Please select a category", color="negative")
                        return
                    
                    try:
                        # Create exact rules for all selected transactions
                        for selected_row in table.selected:
                            tx = selected_row['transaction']
                            create_category_rule(
                                entity=tx['entity'],
                                text=tx['text'],
                                category_name=selected_dropdown.value
                            )
                        
                        ui.notify(f"Created exact rules for {len(table.selected)} transactions", color="positive")
                        load_transactions()
                    except Exception as e:
                        ui.notify(f"Error creating rules: {str(e)}", color="negative")
                
                def assign_entity_only_rules():
                    if not table.selected:
                        ui.notify("Please select transactions first", color="negative") 
                        return
                    if not selected_dropdown.value:
                        ui.notify("Please select a category", color="negative")
                        return
                    
                    try:
                        # Get unique entities from selected transactions
                        entities = set(row['transaction']['entity'] for row in table.selected)
                        
                        # Create entity-only rules (text=null) for each unique entity
                        for entity in entities:
                            create_entity_only_rule(
                                entity=entity,
                                category_name=selected_dropdown.value
                            )
                        
                        ui.notify(f"Created entity-only rules for {len(entities)} entities", color="positive")
                        load_transactions()
                    except Exception as e:
                        ui.notify(f"Error creating entity rules: {str(e)}", color="negative")
                
                # Buttons for different rule types
                with ui.column().classes('gap-2'):
                    ui.button("Assign Exact Rules", 
                             on_click=assign_exact_rules,
                             icon="rule").props('color=primary size=sm')
                    ui.button("Assign Entity Rules", 
                             on_click=assign_entity_only_rules,
                             icon="business").props('color=secondary size=sm')
                
                # Help text
                with ui.column().classes('text-sm text-gray-600 max-w-xs'):
                    ui.label("• Exact Rules: Match entity + text exactly")
                    ui.label("• Entity Rules: Match entity only (default for all transactions from this entity)")


    # Action buttons
    with ui.row().classes('gap-4 mt-4'):
        ui.button("Refresh", on_click=load_transactions).props('outlined')
        
        def apply_all_rules():
            try:
                result = apply_rules_to_transactions()
                message = result.get('message', 'Rules applied successfully')
                
                # Show detailed statistics if available
                if 'stats' in result:
                    stats = result['stats']
                    detailed_msg = (
                        f"{message}\n"
                        f"• Categorized: {stats['categorized']}\n"
                        f"• Uncategorized: {stats['uncategorized']}\n" 
                        f"• Changed: {stats['changed']}"
                    )
                    ui.notify(detailed_msg, color="positive", multi_line=True)
                else:
                    ui.notify(message, color="positive")
                    
                load_transactions()
            except Exception as e:
                ui.notify(f"Error applying rules: {str(e)}", color="negative")
        
        ui.button("Apply All Rules", 
                 on_click=apply_all_rules,
                 icon="auto_fix_high").props('color=accent')
        
        ui.label("Apply existing rules to categorize transactions automatically").classes('text-sm text-gray-600 self-center')

    load_transactions()
