# app/components/navigation.py
from nicegui import ui

def create_navigation():
    """Create the main navigation menu."""
    with ui.header().classes('bg-blue-600'):
        with ui.row().classes('items-center w-full'):
            ui.label('DKBlytics').classes('text-xl font-bold text-white')
            ui.space()  # Push navigation to the right
            
            with ui.row().classes('gap-2'):
                ui.link('Dashboard', '/').classes('text-white hover:text-blue-200 px-3 py-2')
                ui.link('Transactions', '/transactions').classes('text-white hover:text-blue-200 px-3 py-2')
                ui.link('Categories', '/categories').classes('text-white hover:text-blue-200 px-3 py-2')
                ui.link('Balance', '/balance').classes('text-white hover:text-blue-200 px-3 py-2')
                ui.link('Budget', '/budget').classes('text-white hover:text-blue-200 px-3 py-2')

def create_page_layout(title: str):
    """Create a consistent page layout with navigation."""
    create_navigation()
    
    with ui.column().classes('max-w-7xl mx-auto p-6'):
        return ui.column().classes('w-full')  # Return container for page content