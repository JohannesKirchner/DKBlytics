# app/constants.py
"""Constants and configuration values for the frontend."""

# Color schemes for charts
CHART_COLORS = {
    'green': ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'],
    'red': ['#EF4444', '#F87171', '#FCA5A5', '#FECACA', '#FEE2E2'],
    'blue': ['#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE', '#EFF6FF'],
    'purple': ['#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE', '#EDE9FE']
}

# Common CSS classes
CSS_CLASSES = {
    'page_title': 'text-2xl mb-6',
    'section_title': 'text-xl mb-4', 
    'card_title': 'text-lg mb-2',
    'error_text': 'text-red-500',
    'empty_state': 'text-gray-500',
    'control_row': 'gap-4 mb-6 items-end',
    'form_input': 'outlined dense'
}

# Default values
DEFAULTS = {
    'transactions_limit': 50,
    'balance_history_days': 90,
    'chart_height': 400
}