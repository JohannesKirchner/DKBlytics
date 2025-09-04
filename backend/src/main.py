from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .database import initialize_database
from .routers import accounts, transactions, bank, categories, category_rules
from .settings import cors_origins_from_env


PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield  # teardown if needed


# Initialize the FastAPI application
app = FastAPI(
    title="DKBlytics: a modular API to your DKB banking",
    description="A simple API to track personal banking transactions and balances.",
    lifespan=lifespan,
    docs_url=PREFIX + "/docs",
    redoc_url=None,
    openapi_url=PREFIX + "/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_from_env(),      # exact origins only
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],    # add more when needed
    allow_credentials=False,                     # not using cookies
    max_age=3600,
)

# Include the routers to add the API endpoints
app.include_router(accounts.router, prefix=PREFIX)
app.include_router(transactions.router, prefix=PREFIX)
app.include_router(categories.router, prefix=PREFIX)
app.include_router(category_rules.router, prefix=PREFIX)
app.include_router(bank.router, prefix=PREFIX)

# Optional friendly root redirect
@app.get("/api/", include_in_schema=False)
def root():
    return RedirectResponse(url="/api/docs")