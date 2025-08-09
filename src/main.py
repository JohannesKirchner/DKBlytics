from fastapi import FastAPI
from .database import initialize_database
from .routers import accounts, transactions, bank  # , categories


# Initialize the FastAPI application
app = FastAPI(
    title="DKBlytics: a modular API to your DKB banking",
    description="A simple API to track personal banking transactions and balances.",
)


@app.on_event("startup")
def on_startup():
    """
    Initialize the database when the application starts.
    """
    initialize_database()


# Include the routers to add the API endpoints
app.include_router(transactions.router)
# app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(bank.router)
