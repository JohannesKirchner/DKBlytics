# Repository Guidelines

## Project Structure & Module Organization
DKBlytics splits into `backend`, `frontend-nicegui`, and `frontend-svelte`. FastAPI code lives in `backend/src` with routers, services, models, and schema definitions. Database migrations reside in `backend/migrations`, while sample data sits in `backend/data` and `backend/tests/mock_data`. NiceGUI UI logic is grouped under `frontend-nicegui/app/{components,pages,api}`. The SvelteKit prototype lives in `frontend-svelte/src/{routes,lib}`, and shared references stay in `docs/`.

## Build, Test, and Development Commands
- `cd backend && uv venv && source .venv/bin/activate` – create and activate a backend environment.
- `cd backend && uv pip install -e .` – install backend dependencies in editable mode.
- `cd backend && uv run python -m src.main` – start the FastAPI server at `http://localhost:8000/api`.
- `cd backend && uv run pytest` – execute the backend test suite.
- `cd frontend-nicegui && uv run python -m app.main` – launch the NiceGUI dev server on port 8081.
- `cd frontend-svelte && npm install && npm run dev` – start the Svelte dev server (defaults to port 5173).

## Coding Style & Naming Conventions
- Target Python 3.12 with four-space indentation and grouped imports (stdlib, third-party, local).
- Keep request/response contracts in `backend/src/schemas.py` and type-hint new services and routers.
- Name endpoints and functions in `snake_case`; reserve PascalCase for Pydantic models and UI components.
- Use module-level constants (see `backend/src/main.py:13`) for shared prefixes and configuration knobs.
- In the frontends, match file names to route or component intent (`transactions.py`, `BalanceCard.svelte`).

## Testing Guidelines
Pytest with `pytest-order` powers the backend suite; add specs under `backend/tests/endpoints` or feature-specific folders and load fixtures from `backend/tests/mock_data`. Name new files `test_<feature>.py`, parametrize scenarios, and cover both happy-path and error responses. Run focused checks with `uv run pytest -k keyword`, and include regenerated mock payloads or Alembic migrations when behaviour changes.

## Commit & Pull Request Guidelines
Recent commits use short, imperative subjects (`fetch account information`); follow that pattern and reference the touched area when helpful (`backend: add category summary`). Rebase or squash noisy WIP history before opening a PR. Each PR should explain intent, list runtime or test commands you executed, link tracking issues, and provide screenshots or `curl` examples for UI or API changes. Flag schema or data migrations explicitly.

## Security & Configuration Tips
`backend/src/settings.py` loads secrets from `.env`. Provide `DB_PATH`, `DKB_USERNAME`, `DKB_PASSWORD`, optional `DKB_MFA_DEVICE`, and a 32-byte `IBAN_HMAC_KEY` (hex or base64). Never commit real credentials; update `.env.example` when requirements shift. Default local storage writes to `.data/app.db`, so scrub it before sharing datasets. Update `FRONTEND_ORIGINS` when exposing the API beyond localhost to keep CORS aligned with deployments.
