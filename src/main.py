from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import initialize_database
from .routers import accounts, transactions, bank, categories, category_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield  # teardown if needed


# Initialize the FastAPI application
app = FastAPI(
    title="DKBlytics: a modular API to your DKB banking",
    description="A simple API to track personal banking transactions and balances.",
    lifespan=lifespan,
)

# Include the routers to add the API endpoints
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(category_rules.router)
app.include_router(bank.router)
