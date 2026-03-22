# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DKBlytics is a full-stack banking analytics application that processes DKB (Deutsche Kreditbank) transaction data. It consists of:

- **Backend**: FastAPI REST API (`backend/`) with SQLite database 
- **Frontend**: SvelteKit application (`frontend/`) with TailwindCSS and Chart.js

## Architecture

### Backend (FastAPI)
- **Entry point**: `backend/src/main.py` - FastAPI app with CORS and route registration
- **Database**: SQLAlchemy ORM with SQLite, initialized via `database.py`
- **Routes**: Organized in `src/routers/` (accounts, transactions, categories, category_rules, balances, bank)
- **Business logic**: `src/services/` layer matches router structure
- **Models**: `src/models.py` (SQLAlchemy) and `src/schemas.py` (Pydantic)
- **Settings**: `src/settings.py` handles configuration including CORS origins

### Frontend (SvelteKit)
- **Routes**: File-based routing in `src/routes/`
- **API client**: `src/lib/api.js` provides `apiFetch` wrapper for backend communication
- **Components**: Reusable UI components in `src/lib/components/`
- **Server-side data**: Uses `+page.server.js` files for data fetching

### Banking Integration
- **CSV Import**: Upload DKB CSV exports via `POST /api/bank/import_csv` (multipart form: `file`, `holder_name`, `parser_type`)
- **Parser Architecture**: `src/services/csv_parsers/` — `base.py` defines `CSVParser` ABC and `ParsedBankData`, `registry.py` holds a global `ParserRegistry`, `dkb_parser.py` is the only built-in parser
- **Adding parsers**: Subclass `CSVParser`, implement `name`, `bank_name`, `can_parse()`, and `parse()`, then register in `ParserRegistry._register_built_in_parsers()`
- **Bank models**: `src/services/bank_models.py` defines `BankAccount` and `BankTransaction` as intermediary models between CSV data and DB models

## Development Commands

### Backend
```bash
cd backend
# Setup
uv venv && source .venv/bin/activate
uv pip install -e .

# Run development server
python -m src.main
# API available at http://localhost:8000
# Docs at http://localhost:8000/api/docs

# Testing
pytest tests/ -v
pytest tests/endpoints/test_accounts.py::test_create_account -v  # Single test
pytest tests/ --cov=src --cov-report=html                      # With coverage
```

### Frontend
```bash
cd frontend
# Development
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview build

# Code quality
npm run format       # Prettier formatting
npm run lint         # ESLint + Prettier check
```

## Database

- **SQLite database**: Created automatically on first backend startup via `initialize_database()`
- **Migration tool**: Alembic configured in `backend/alembic/` (though manual schema changes work for development)
- **Test isolation**: Tests use temporary SQLite files with session-scoped fixtures

## Testing Strategy

### Sequential Test Execution
- Tests use `@pytest.mark.order()` to enforce execution sequence
- **Session-scoped fixtures** maintain state across tests for realistic data flow
- Tests are designed as **happy path integration tests** that build on each other's state

### Test Order
1. **Accounts** (orders 1-3): Create base account structure
2. **Transactions** (orders 4-30): Create transaction data
3. **Categories** (orders 20-25): Set up category hierarchies
4. **Category Rules** (orders 26-39): Configure categorization rules  
5. **Bank Integration** (orders 40-42): Test CSV import
6. **Balances** (orders 50-55): Test balance calculations and analytics

### Running Tests
```bash
# Full suite (sequential execution)
pytest tests/ -v

# Individual modules (may require setup from earlier tests)
pytest tests/endpoints/test_accounts.py -v
pytest tests/endpoints/test_balances.py -v

# Test debugging
pytest tests/endpoints/test_bank.py::test_update_from_bank -v -s
```

## Key Features

### Transaction Management
- **CSV Import**: DKB CSV exports parsed by pluggable parser system; no live bank API
- **Duplicate Detection**: Batch-aware duplicate prevention using transaction fingerprints
- **Categorization**: Rule-based automatic categorization with entity matching

### Balance Analytics
- **Historical Accuracy**: Time-series balance tracking with transaction-level precision
- **Multiple Granularities**: Daily, weekly, monthly, yearly, and fiscal period analysis
- **Multi-account Support**: Combined and per-account balance tracking
- **Surplus Calculations**: Income vs expense flow analysis

### API Design
- **REST endpoints** with `/api` prefix
- **Consistent error handling** with appropriate HTTP status codes
- **Pydantic validation** for all request/response models
- **OpenAPI documentation** auto-generated at `/api/docs`

## Important Implementation Details

### Date Handling
- Backend `_parse_date()` function supports multiple formats: DD.MM.YYYY, YYYY-MM-DD
- Flexible parsing for bank data compatibility

### IBAN Security  
- IBANs are HMAC-hashed in database for privacy
- Original IBAN passed in API but stored as hash for lookup

### Bank Integration Architecture
- **Error resilience**: Graceful handling of malformed bank data
- **Batch tracking**: Each import run gets unique batch hash for duplicate detection

### Test Data Management
- **Mock data**: JSON files in `tests/mock_data/` for consistent test scenarios
- **Fixture hierarchy**: Session-scoped fixtures with conditional seeding logic