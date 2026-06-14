# Budget Page — Implementation Plan

Status: **design locked, backend not yet implemented**. The frontend design (`mockup-1a`)
is built and runs on throwaway mock data. This document is the plan to wire it to the
backend.

---

## 1. Chosen design

- Route prototype: `frontend/src/routes/budget/mockup-1a/+page.svelte`
- Mock data + helpers (to be deleted once wired): `frontend/src/lib/budgetMock.js`
- Layout: large left **Sankey** (Income → Expenses + Savings, with sub-categories on
  both sides), right column = full-history **category time-series** (with €-valued
  y-axis) on top + **expense composition donut** below.
- **Savings is NOT a category** with transactions. It is purely the delta
  `Income − Expenses`, shown as a synthetic node branching off the Income total.
- Period modes: `year` (sum), `avgYear` (average), `month` (single month) + month picker.
- The "over time" panel **always** shows full history since the earliest record,
  independent of the selected period.

### Frontend layout gotchas (learned the hard way)
Use **inline `style`** — not arbitrary Tailwind values — for:
- page height: `style="height: calc(100vh - 48px)"` (Tailwind `h-[calc(100vh-3rem)]`
  emits invalid CSS because `calc` needs spaces around `-`; underscores are required and
  even then JIT/stale-tab issues bite).
- column widths: `style="flex: 0 0 55%"` / `style="flex: 1 1 0; min-width: 0"`.
- pie size: `style="height: 140px; width: 140px"` (arbitrary `max-h-[150px]` silently
  failed to apply).
The Sankey fills its panel by measuring it via `bind:clientWidth`/`bind:clientHeight`
(no `preserveAspectRatio="meet"`, which letterboxes).

---

## 2. Backend findings (what already exists)

- **Income/Expense split is structural**: two protected root categories,
  **`Einnahmen`** (income) and **`Ausgaben`** (expenses), seeded in
  `backend/src/services/categories.py`. Every category descends from one of them.
- `transaction.amount` is **signed** (`+` inflow, `−` outflow).
- Categories form a real tree (`Category.parent_id`), exposed via `GET /categories/tree`.
- **`transaction.category_id` is persisted and kept current**: set at import/update via
  the rules engine, and `services/category_rules.py` re-resolves affected transactions
  whenever rules change. → Budget aggregations can safely `GROUP BY category_id`.
  Uncategorized = `category_id IS NULL`.
- Reusable pieces:
  - `GET /transactions/summary?scope_name=&depth=&date_from=&date_to=&account_id=&q=`
    groups by one category depth within a scope — but returns the **full transactions
    list per group** (heavy) and only one level.
  - `services/balances.py` has date-bucketing helpers (monthly/yearly) — balance/surplus
    only, not per-category.

### Gaps (no endpoint provides today)
1. The **whole Sankey flow** in one lightweight call.
2. A **per-category time series** (monthly subtree sums across full history).

---

## 3. Backend changes to build

New `budget` router + service + schemas; register the router in `backend/src/main.py`.

### 3.1 `GET /api/budget/sankey`
Drives the Sankey **and** the donut **and** the KPIs (frontend derives the latter two
from this payload).

Params: `date_from`, `date_to`, `account_id?`.

Core structure (two total nodes + a synthetic Savings node):
```
income subcats → income cats → [income] → [expenses] → expense cats → expense subcats
                                [income] → [savings]
```

Implementation:
- One aggregate: `SELECT category_id, SUM(amount) FROM transactions WHERE date in range
  [+account] GROUP BY category_id`, plus a sign-split `NULL` bucket for uncategorized.
- Roll leaf sums up the category tree to subtree totals per node.
- **Full depth, generic**: emit a `node → parent` link for every level. Each node carries
  `side` (`income` | `center` | `expense`) and `depth`; the frontend `layoutSankey` maps
  `depth → column`, so arbitrarily deep trees work.
- Two synthetic core nodes: **`income`** (total income) and **`expenses`** (total
  expenses). Top-level income categories link `cat → income`; `expenses → cat` for
  top-level expense categories.
- Core links: `income → expenses` (value = total expenses) and
  `income → savings` (value = `income − expenses`, **only when ≥ 0**).
- **`savings`** is a synthetic node — never a category, no transactions; value = the delta.
- Uncategorized inflows → "Other income" (→ `income`); outflows → "Other" (`expenses` →).
- Deficit case (`expenses > income`): no `savings` node; either show a "Deficit/Drawdown"
  source feeding `expenses`, or cap. **Decide at build time.**
- Note: a parent with its own direct transactions may have a node value larger than the
  sum of its child links — that's fine; the Sankey uses `max(in, out)` for node height.

Response shape:
```json
{
  "nodes": [
    {"id": "cat:12",  "label": "Salary",   "side": "income",  "depth": 1},
    {"id": "income",  "label": "Income",   "side": "center",  "depth": 0},
    {"id": "expenses","label": "Expenses", "side": "center",  "depth": 0},
    {"id": "savings", "label": "Savings",  "side": "income",  "depth": 0},
    {"id": "cat:30",  "label": "Housing",  "side": "expense", "depth": 1},
    {"id": "other_out","label": "Other",   "side": "expense", "depth": 1}
  ],
  "links": [
    {"source": "cat:1",   "target": "cat:12",   "value": 3000},
    {"source": "cat:12",  "target": "income",   "value": 3400},
    {"source": "income",  "target": "expenses", "value": 2850},
    {"source": "income",  "target": "savings",  "value": 1350},
    {"source": "expenses","target": "cat:30",   "value": 1350},
    {"source": "cat:30",  "target": "cat:41",   "value": 1100}
  ],
  "totals": { "income": 4200, "expenses": 2850, "savings": 1350 },
  "meta": { "months_with_data": 12 }
}
```

`meta.months_with_data` = count of distinct `YYYY-MM` with ≥1 transaction in the range
(account-filtered). Used for average mode (see §4).

### 3.2 `GET /api/budget/category-series`
Drives the "over time" panel.

Params: `category_id` (or `uncategorized`), `account_id?`, `granularity=monthly|yearly`
(default `monthly`), optional `date_from`/`date_to` (default = full history).

Implementation: resolve the category's subtree (ids incl. descendants), sum per bucket
from the earliest record to the latest, fill empty buckets with 0.

Response:
```json
[ {"date": "2023-01-01", "value": 480}, {"date": "2023-02-01", "value": 520} ]
```

### 3.3 Schemas (`backend/src/schemas.py`)
`SankeyNode`, `SankeyLink`, `SankeyResponse` (nodes + links + totals + meta),
`CategorySeriesPoint`.

### 3.4 Optional
Add `include_transactions: bool = False` to `/transactions/summary` so it can be reused
without the heavy payload. **Not required** — the Sankey endpoint already covers
donut + KPIs.

### 3.5 Tests
Ordered integration tests (~orders 56–60) following the existing happy-path pattern in
`backend/tests/`.

---

## 4. Period modes = frontend date-math (no backend work)

The backend only needs `date_from`/`date_to`. The frontend computes:
- `year` → full calendar-year range; values as returned.
- `month` → single-month range.
- **`average/year` → period values ÷ `meta.months_with_data`** (NOT ÷ 12), so partial /
  current years aren't understated.

The time-series panel always requests full history regardless of the selected period.

---

## 5. Frontend wiring (after backend is up)

- Add `frontend/src/routes/budget/+page.server.js`: load `/api/budget/sankey` for the
  initial period + `/api/budget/category-series` for a default category + accounts list.
- Move `mockup-1a/+page.svelte` to the real `budget/+page.svelte`; replace `budgetMock.js`
  imports with the loaded data. Re-fetch the series on category hover/click and the Sankey
  on period change (client-side, URL-synced like `balance/+page.server.js`).
- Keep the SVG Sankey / donut / line-chart renderers and the `layoutSankey` helper.
- Delete `frontend/src/lib/budgetMock.js` and the `mockup-1a` route.

---

## 6. Open assumptions to validate

- Aggregating on stored `transaction.category_id` (kept current by the rules engine) —
  consistent with `/transactions/summary`.
- A category could in principle hold both inflows and outflows; nodes are classified by
  their root (`Einnahmen`/`Ausgaben`), uncategorized by sign.
- Combined accounts by default; `account_id` filter optional.
- Performance: one `GROUP BY` query per endpoint — fine for SQLite.
