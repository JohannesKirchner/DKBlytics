# app/pages/transactions.py
from nicegui import ui
from app.api.transactions import get_transactions, update_transaction
from app.api.category_rules import create_category_rule, create_entity_only_rule, create_transaction_rule, apply_rules_to_transactions
from app.components.category_dropdown import category_dropdown
from app.utils import create_empty_state, create_loading_accounts_dropdown, create_date_inputs
from app.constants import CSS_CLASSES, DEFAULTS
from typing import Dict, Any, Optional
import math


def render_transactions_page():
    ui.label("Transactions").classes(CSS_CLASSES['page_title'])
    render_transactions_section()


def render_transactions_section():
    """Render the main transactions section with filtering, categorization, and pagination."""
    
    # Filter controls
    controls_container = ui.column().classes('mb-4')
    
    # Results and pagination
    table_container = ui.column()
    pagination_container = ui.row().classes('justify-center items-center gap-4 mt-4')
    
    # Current filter state
    current_filters = {
        'limit': 50,
        'offset': 0,
        'sort_by': 'date_desc',
        'date_from': None,
        'date_to': None,
        'account_id': None,
        'category': None,
        'q': None
    }
    
    def load_transactions():
        """Load transactions with current filters and pagination."""
        table_container.clear()
        pagination_container.clear()
        
        try:
            response = get_transactions(**current_filters)
            transactions = response.get("items", [])
            total = response.get("total", 0)
            limit = response.get("limit", 50)
            offset = response.get("offset", 0)
            
            if not transactions:
                create_empty_state(table_container, "No transactions found")
                return
            
            # Build table rows with all columns
            rows = []
            for tx in transactions:
                # Safely format amount - handle both string and numeric types
                amount = tx['amount']
                if isinstance(amount, str):
                    try:
                        amount = float(amount)
                    except ValueError:
                        amount = 0.0
                formatted_amount = f"{amount:.2f}€"
                
                rows.append({
                    'id': tx['id'],
                    'date': tx['date'],
                    'account_name': tx.get('account_name', ''),
                    'entity': tx['entity'],
                    'text': tx.get('text', ''),
                    'amount': formatted_amount,
                    'category': tx.get('category') or 'Uncategorized',
                    'reference': tx.get('reference', ''),
                    'transaction': tx  # Keep full transaction for reference
                })
            
            with table_container:
                # Create table with all columns including actions
                table = ui.table(
                    columns=[
                        {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
                        {'name': 'account_name', 'label': 'Account', 'field': 'account_name', 'sortable': True},
                        {'name': 'entity', 'label': 'Entity', 'field': 'entity', 'sortable': True},
                        {'name': 'text', 'label': 'Description', 'field': 'text'},
                        {'name': 'amount', 'label': 'Amount', 'field': 'amount', 'sortable': True},
                        {'name': 'category', 'label': 'Category', 'field': 'category'},
                        {'name': 'reference', 'label': 'Reference', 'field': 'reference'},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions'},
                    ],
                    rows=rows,
                    row_key='id',
                    selection='multiple'
                ).classes('w-full')
                
                # Configure table properties for better display
                table.props('dense flat bordered')
                
                # Add edit functionality with a custom slot for actions
                def create_edit_dialog(tx_data):
                    """Create edit dialog for a transaction."""
                    with ui.dialog() as dialog, ui.card().style('min-width: 400px'):
                        ui.label('Edit Transaction').classes('text-h6 mb-4')
                        
                        # Create form inputs with current values
                        entity_input = ui.input(
                            label='Entity',
                            value=tx_data.get('entity', ''),
                            placeholder='Enter entity name...'
                        ).props('filled').classes('mb-2')
                        
                        text_input = ui.input(
                            label='Description',
                            value=tx_data.get('text', ''),
                            placeholder='Enter transaction description...'
                        ).props('filled').classes('mb-4')
                        
                        # Readonly fields for context
                        ui.label(f"Amount: {tx_data.get('amount', '')}")
                        ui.label(f"Date: {tx_data.get('date', '')}")
                        ui.label(f"Account: {tx_data.get('account_name', '')}")
                        ui.separator().classes('my-4')
                        
                        # Action buttons
                        with ui.row().classes('gap-2 justify-end'):
                            ui.button('Cancel', 
                                     on_click=dialog.close).props('flat')
                            
                            def save_changes():
                                try:
                                    # Only send changes that differ from original
                                    entity_changed = entity_input.value != tx_data.get('entity', '')
                                    text_changed = text_input.value != tx_data.get('text', '')
                                    
                                    if not entity_changed and not text_changed:
                                        ui.notify('No changes to save', color='info')
                                        dialog.close()
                                        return
                                    
                                    # Update transaction
                                    update_data = {}
                                    if entity_changed:
                                        update_data['entity'] = entity_input.value
                                    if text_changed:
                                        update_data['text'] = text_input.value
                                    
                                    update_transaction(tx_data['id'], **update_data)
                                    ui.notify('Transaction updated successfully', color='positive')
                                    dialog.close()
                                    load_transactions()  # Refresh the table
                                    
                                except Exception as e:
                                    ui.notify(f'Error updating transaction: {str(e)}', color='negative')
                            
                            ui.button('Save', 
                                     on_click=save_changes).props('color=primary')
                    
                    return dialog
                
                # Add action buttons using table slot
                table.add_slot('body-cell-actions', '''
                    <q-td key="actions" :props="props">
                        <q-btn flat round color="primary" icon="edit" size="sm"
                               @click="$parent.$emit('edit-transaction', props.row)" />
                    </q-td>
                ''')
                
                # Handle edit button clicks
                def handle_edit(e):
                    tx_data = e.args
                    dialog = create_edit_dialog(tx_data['transaction'])
                    dialog.open()
                
                table.on('edit-transaction', handle_edit)
                
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
                    
                    def assign_transaction_rules():
                        if not table.selected:
                            ui.notify("Please select transactions first", color="negative") 
                            return
                        if not selected_dropdown.value:
                            ui.notify("Please select a category", color="negative")
                            return
                        
                        try:
                            # Create transaction-specific rules for each selected transaction
                            for selected_row in table.selected:
                                tx = selected_row['transaction']
                                create_transaction_rule(
                                    transaction_id=tx['id'],
                                    category_name=selected_dropdown.value
                                )
                            
                            ui.notify(f"Created transaction rules for {len(table.selected)} transactions", color="positive")
                            load_transactions()
                        except Exception as e:
                            ui.notify(f"Error creating transaction rules: {str(e)}", color="negative")
                    
                    # Buttons for different rule types
                    with ui.column().classes('gap-2'):
                        ui.button("Assign Exact Rules", 
                                 on_click=assign_exact_rules,
                                 icon="rule").props('color=primary size=sm')
                        ui.button("Assign Entity Rules", 
                                 on_click=assign_entity_only_rules,
                                 icon="business").props('color=secondary size=sm')
                        ui.button("Assign Transaction Rules", 
                                 on_click=assign_transaction_rules,
                                 icon="person_pin").props('color=accent size=sm')
                    
                    # Help text
                    with ui.column().classes('text-sm text-gray-600 max-w-xs'):
                        ui.label("• Exact Rules: Match entity + text exactly")
                        ui.label("• Entity Rules: Match entity only (default for all transactions from this entity)")
                        ui.label("• Transaction Rules: Apply category to this specific transaction only (highest priority)")
            
            # Create pagination controls
            create_pagination_controls(total, limit, offset, pagination_container, load_transactions, current_filters)
            
        except Exception as e:
            create_empty_state(table_container, f"Error loading transactions: {str(e)}")
    
    # Create filter controls
    create_transaction_filters(controls_container, current_filters, load_transactions)
    
    # Action buttons for rule management 
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

    # Initial load
    load_transactions()


def create_transaction_filters(container, filters: Dict, reload_callback):
    """Create comprehensive filter controls for transactions."""
    with container:
        ui.label("Filters").classes(CSS_CLASSES['card_title'])
        
        with ui.card().classes('p-4'):
            with ui.grid(columns=4).classes('gap-4 items-end'):
                # Date range
                date_from, date_to = create_date_inputs(30)  # Default last 30 days
                date_from.bind_value(filters, 'date_from')
                date_to.bind_value(filters, 'date_to')
                
                # Account selection
                account_select = create_loading_accounts_dropdown("Account")
                account_select.bind_value(filters, 'account_id')
                
                # Category selection
                category_options = ['', 'null']  # Empty for all, 'null' for uncategorized
                try:
                    from app.api.categories import get_all_categories
                    categories = get_all_categories()
                    category_options.extend([cat['name'] for cat in categories])
                except:
                    pass
                
                category_select = ui.select(
                    options=category_options,
                    label="Category"
                ).props(CSS_CLASSES['form_input'])
                category_select.bind_value(filters, 'category')
                
                # Sort by
                sort_options = {
                    'date_desc': 'Date (Newest)',
                    'date_asc': 'Date (Oldest)',
                    'amount_desc': 'Amount (High to Low)',
                    'amount_asc': 'Amount (Low to High)'
                }
                sort_select = ui.select(
                    options=sort_options,
                    label="Sort By",
                    value='date_desc'
                ).props(CSS_CLASSES['form_input'])
                sort_select.bind_value(filters, 'sort_by')
                
                # Search query
                search_input = ui.input(
                    label="Search",
                    placeholder="Search in entity, text, reference..."
                ).props(CSS_CLASSES['form_input'])
                search_input.bind_value(filters, 'q')
                
                # Page size
                limit_select = ui.select(
                    options=[25, 50, 100, 200],
                    label="Per Page",
                    value=50
                ).props(CSS_CLASSES['form_input'])
                limit_select.bind_value(filters, 'limit')
                
                # Apply filters button
                def apply_filters():
                    filters['offset'] = 0  # Reset to first page
                    reload_callback()
                
                ui.button("Apply Filters", 
                         on_click=apply_filters,
                         icon="search").props('color=primary')
                
                # Clear filters button
                def clear_filters():
                    filters.update({
                        'offset': 0,
                        'date_from': None,
                        'date_to': None,
                        'account_id': None,
                        'category': None,
                        'q': None,
                        'sort_by': 'date_desc'
                    })
                    reload_callback()
                
                ui.button("Clear", 
                         on_click=clear_filters,
                         icon="clear").props('outlined')


def create_pagination_controls(total: int, limit: int, offset: int, container, reload_callback, filters):
    """Create pagination controls."""
    if total <= limit:
        return  # No pagination needed
    
    current_page = offset // limit + 1
    total_pages = math.ceil(total / limit)
    
    with container:
        # Previous button
        def go_previous():
            if current_page > 1:
                filters['offset'] = (current_page - 2) * limit
                reload_callback()
        
        ui.button("Previous", 
                 on_click=go_previous,
                 icon="chevron_left").props('outline').set_enabled(current_page > 1)
        
        # Page info
        ui.label(f"Page {current_page} of {total_pages} ({total} total)")
        
        # Next button  
        def go_next():
            if current_page < total_pages:
                filters['offset'] = current_page * limit
                reload_callback()
        
        ui.button("Next",
                 on_click=go_next,
                 icon="chevron_right").props('outline').set_enabled(current_page < total_pages)
        
        # Jump to page input
        with ui.row().classes('items-center gap-2'):
            ui.label("Go to page:")
            page_input = ui.number(label="", value=current_page, min=1, max=total_pages).classes('w-20')
            
            def jump_to_page():
                page = int(page_input.value or 1)
                page = max(1, min(page, total_pages))
                filters['offset'] = (page - 1) * limit
                reload_callback()
            
            ui.button("Go", on_click=jump_to_page).props('size=sm')