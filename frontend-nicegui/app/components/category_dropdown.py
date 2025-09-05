# app/components/category_dropdown.py
from nicegui import ui
from app.api.categories import get_all_categories
from typing import Callable, Optional


def category_dropdown(on_change: Optional[Callable] = None, label: str = "Category") -> ui.select:
    """Create a category dropdown populated from the API.
    
    Args:
        on_change: Optional callback for value changes
        label: Label for the dropdown
        
    Returns:
        Configured select element
    """
    try:
        categories = get_all_categories()
        options = [c["name"] for c in categories]
    except Exception as e:
        ui.notify(f"Error loading categories: {str(e)}", color="negative")
        options = []

    dropdown = ui.select(options, label=label, on_change=on_change)
    dropdown.props('outlined dense')
    return dropdown
