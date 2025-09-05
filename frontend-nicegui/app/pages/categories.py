# app/pages/categories.py
from nicegui import ui
from app.api.categories import get_all_categories, create_category, delete_category
from app.api.category_rules import get_all_category_rules, delete_category_rule
from app.components.category_dropdown import category_dropdown
from app.utils import create_empty_state, create_error_message
from app.constants import CSS_CLASSES

def render_categories_page():
    """Render the categories management page."""
    ui.label("Category Management").classes(CSS_CLASSES['page_title'])
    
    # Tab container for different views
    with ui.tabs() as tabs:
        categories_tab = ui.tab('categories', label='Categories', icon='folder')
        rules_tab = ui.tab('rules', label='Category Rules', icon='rule')
    
    with ui.tab_panels(tabs, value='categories'):
        # Categories Tab
        with ui.tab_panel(categories_tab):
            _render_categories_section()
        
        # Rules Tab  
        with ui.tab_panel(rules_tab):
            _render_rules_section()

def _render_categories_section():
    """Render the categories management section."""
    ui.label("Categories").classes(CSS_CLASSES['section_title'])
    
    # Create category form
    with ui.card().classes('mb-6'):
        ui.label("Add New Category").classes(CSS_CLASSES['card_title'])
        with ui.row().classes('gap-4 items-end'):
            name_input = ui.input("Category Name").props(CSS_CLASSES['form_input'])
            parent_dropdown = category_dropdown(label="Parent Category (optional)")
            
            def create_new_category():
                if not name_input.value:
                    ui.notify("Please enter a category name", color="negative")
                    return
                    
                try:
                    parent_name = parent_dropdown.value if parent_dropdown.value else None
                    create_category(name_input.value, parent_name)
                    ui.notify(f"Category '{name_input.value}' created successfully", color="positive")
                    name_input.value = ""
                    parent_dropdown.value = None
                    load_categories()
                except Exception as e:
                    ui.notify(f"Error creating category: {str(e)}", color="negative")
            
            ui.button("Create Category", on_click=create_new_category).props('color=primary')
    
    # Categories table
    categories_container = ui.column().classes('w-full')
    
    def load_categories():
        categories_container.clear()
        
        try:
            categories = get_all_categories()
            
            if not categories:
                create_empty_state(categories_container, "No categories found")
                return
            
            # Build table data
            rows = []
            for cat in categories:
                rows.append({
                    'name': cat['name'],
                    'parent': cat.get('parent_name', 'Root'),
                    'id': cat['id'],
                    'actions': '',  # Will be replaced with buttons
                    'category': cat  # Keep full object for actions
                })
            
            with categories_container:
                table = ui.table(
                    columns=[
                        {'name': 'name', 'label': 'Name', 'field': 'name'},
                        {'name': 'parent', 'label': 'Parent', 'field': 'parent'},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions'},
                    ],
                    rows=rows,
                    row_key='name'
                ).classes('w-full')
                
                def delete_cat(e):
                    # Extract category name from event arguments
                    category_name = e.args if hasattr(e, 'args') else str(e)
                    try:
                        delete_category(category_name)
                        ui.notify(f"Category '{category_name}' deleted", color="positive")
                        load_categories()
                    except Exception as e:
                        ui.notify(f"Error deleting category: {str(e)}", color="negative")
                
                # Actions column - use template for proper row access
                table.add_slot('body-cell-actions', '''
                    <q-td key="actions" :props="props">
                        <q-btn 
                            size="sm" 
                            color="negative" 
                            label="Delete" 
                            @click="$parent.$emit('delete_category', props.row.name)"
                        />
                    </q-td>
                ''')
                
                table.on('delete_category', delete_cat)
                        
        except Exception as e:
            create_error_message(categories_container, f"Error loading categories: {str(e)}")
    
    load_categories()

def _render_rules_section():
    """Render the category rules management section."""
    ui.label("Category Rules").classes(CSS_CLASSES['section_title'])
    ui.label("Rules automatically assign transactions to categories based on entity and text patterns.").classes('text-gray-600 mb-4')
    
    rules_container = ui.column().classes('w-full')
    
    def load_rules():
        rules_container.clear()
        
        try:
            rules = get_all_category_rules()
            
            if not rules:
                create_empty_state(rules_container, "No category rules found")
                return
            
            # Build table data
            rows = []
            for rule in rules:
                rows.append({
                    'id': rule['id'],
                    'entity': rule['entity'],
                    'text': rule['text'] or '(default for entity)',
                    'category': rule['category_name'],
                    'actions': '',  # Will be replaced with buttons
                    'rule': rule  # Keep full object for actions
                })
            
            with rules_container:
                table = ui.table(
                    columns=[
                        {'name': 'entity', 'label': 'Entity', 'field': 'entity'},
                        {'name': 'text', 'label': 'Text Pattern', 'field': 'text'},
                        {'name': 'category', 'label': 'Category', 'field': 'category'},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions'},
                    ],
                    rows=rows,
                    row_key='id'
                ).classes('w-full')
                
                def delete_rule(e):
                    # Extract rule ID from event arguments
                    rule_id = e.args if hasattr(e, 'args') else str(e)
                    try:
                        delete_category_rule(rule_id)
                        ui.notify("Category rule deleted", color="positive")
                        load_rules()
                    except Exception as e:
                        ui.notify(f"Error deleting rule: {str(e)}", color="negative")
                
                # Actions column - use template for proper row access
                table.add_slot('body-cell-actions', '''
                    <q-td key="actions" :props="props">
                        <q-btn 
                            size="sm" 
                            color="negative" 
                            label="Delete" 
                            @click="$parent.$emit('delete_rule', props.row.id)"
                        />
                    </q-td>
                ''')
                
                table.on('delete_rule', delete_rule)
        
        except Exception as e:
            create_error_message(rules_container, f"Error loading rules: {str(e)}")
    
    load_rules()
    
    ui.button("Refresh Rules", on_click=load_rules).classes('mt-4')