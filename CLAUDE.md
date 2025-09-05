# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DKBlytics is a personal banking analytics application that integrates with DKB (Deutsche Kreditbank) to track transactions, categorize expenses, and provide budget insights. The project consists of:

- **Backend**: FastAPI-based REST API with SQLite database
- **Frontend**: NiceGUI web application for user interface

## Architecture

### Backend (FastAPI + SQLAlchemy)
- **Entry Point**: `backend/src/main.py` - FastAPI application with CORS middleware
- **Database**: SQLite with SQLAlchemy ORM, models defined in `backend/src/models.py`
- **Core Models**: 
  - `Account`: Bank accounts with IBAN hashing for privacy
  - `Transaction`: Financial transactions with categorization support
  - `Category`: Hierarchical expense/income categories
  - `CategoryRule`: Automatic categorization rules based on entity/text patterns
- **API Structure**: Modular routers in `backend/src/routers/` for each resource
- **Services**: Business logic in `backend/src/services/` including DKB integration
- **Database Setup**: `backend/src/database.py` handles SQLite connection and session management

### Frontend (NiceGUI)
- **Entry Point**: `frontend-nicegui/app/main.py` - Main UI application
- **Page Structure**: Modular pages in `frontend-nicegui/app/pages/`
- **Components**: Reusable UI components in `frontend-nicegui/app/components/`
- **API Integration**: Client modules in `frontend-nicegui/app/api/`
- **Pages**: Dashboard, categorization, categories management, balance tracking, budget overview

## Development Commands

### Backend
```bash
cd backend
# Install dependencies
uv install

# Run development server
uv run python -m uvicorn src.main:app --reload --port 8000

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/endpoints/test_transactions.py -v
```

### Frontend
```bash
cd frontend-nicegui
# Run development server (requires backend running)
python app/main.py
# Or with uv
uv run python app/main.py
```

## Database

- **Location**: `backend/data/database.sqlite`
- **Migrations**: Handled by SQLAlchemy `create_all()` on startup
- **Privacy**: IBANs are stored as HMAC-SHA256 hashes with only last 4 digits visible
- **Foreign Keys**: Enforced with SQLite pragma for data integrity

## Key Features

1. **DKB Integration**: Automated transaction fetching via `dkb-robo` library
2. **Transaction Categorization**: Manual and rule-based automatic categorization
3. **Hierarchical Categories**: Parent-child category relationships
4. **Privacy-First**: Sensitive account data is hashed/masked
5. **Real-time UI**: NiceGUI provides reactive web interface

## Testing

- **Backend Tests**: Located in `backend/tests/`
- **Mock Data**: JSON fixtures in `backend/tests/mock_data/`
- **Test Structure**: Organized by endpoint (`test_accounts.py`, `test_transactions.py`, etc.)
- **Test Configuration**: `backend/tests/conftest.py` sets up test database

## API Documentation

- **Swagger UI**: Available at `http://localhost:8000/api/docs` when backend is running
- **Base URL**: All API endpoints prefixed with `/api`
- **CORS**: Configured for cross-origin requests from frontend

## Development Notes

- **Virtual Environment**: Backend uses `uv` for dependency management
- **Port Configuration**: Backend on 8000, Frontend on 8080
- **Database Initialization**: Automatically creates tables on first run
- **Privacy Considerations**: Never expose raw IBAN data in API responses