# Frontend Expansion Ideas

These routes are currently on hold but remain viable candidates if we broaden the scope beyond the initial four screens.

- **Dashboard**: Snapshot of balances, recent uncategorized transactions, and quick links into detailed modules.
- **Rules Library**: Centralized review of categorization rules, conflict detection, and batch testing before applying changes.
- **Accounts & Integrations**: Manage DKB account connections, manual metadata tweaks, and token refresh workflows.
- **Data Import**: Guided CSV uploader with schema validation, preview, and confirmation before committing transactions.
- **Insights & Reports**: Saved analytics views (top merchants, recurring charges, heatmaps) with options to export summaries.
- **Goals & Forecasts**: Visualize savings targets or debt payoff projections derived from historical activity.
- **Settings & Preferences**: Configure currency display, default date ranges, and API keys; reference `.env` requirements from `backend/src/settings.py`.
- **Audit Log**: Track categorization changes, imports, and bulk actions to aid collaboration and compliance.

Revisit this list after the core Svelte routes are in place to prioritize the next wave of features.

## Core Route Plans

### Balance
Landing view with an account switcher, preset ranges (30d/90d/1y/custom), and stacked area/line charts fed by `/api/accounts` and `/api/transactions?sort_by=date_desc`. Include KPI cards for current balance and month-to-date change, a transaction sidebar showing the latest movements, CSV export for the active range, and persistence of filters in local storage.

### Categories
Tree editor backed by `/api/categories` supporting drag-and-drop reparenting, inline rename, usage counts populated from `/api/transactions?category=...`, and create/edit modals that enforce unique sibling names. Surface rule assignments per category and present a diff preview before confirming structural changes.

### Transaction Categorization
Paginated data grid with multi-select and column filters mirroring API parameters (`date_from`, `date_to`, `account_id`, `category`, `q`). Provide a rule suggestion panel for creating exact/entity rules through `/api/category-rules`, bulk apply/undo actions, real-time badges for uncategorized entries, and an activity log drawer documenting batch changes.

### Budget
Monthly and annual tabs drawing on aggregated totals (extend the backend if needed), budget cards with progress bars and variance tags, and a calendar heatmap highlighting spending streaks. Offer forms to create or adjust budgets, scenario toggles (baseline vs stretch), and alerting when thresholds are breached.
