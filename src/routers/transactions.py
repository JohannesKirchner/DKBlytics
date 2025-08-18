from typing import Optional, Literal
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from ..models import Transaction, PaginatedTransactions
from ..crud import (
    get_transaction_by_id,
    create_transaction_db,
    get_all_transactions_db,
    count_transactions_db,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Transaction, status_code=201)
def create_transaction(transaction: Transaction):
    """
    Adds a new transaction to the database.
    """
    transaction_id = create_transaction_db(transaction)
    return {**transaction.dict(), "transaction_id": transaction_id}


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: int):
    """
    Retrieves a single transaction by its ID.
    """
    transaction_data = get_transaction_by_id(transaction_id)
    if transaction_data:
        return Transaction(**dict(transaction_data))
    raise HTTPException(status_code=404, detail="Transaction not found")


@router.get("/", response_model=PaginatedTransactions)
def get_all_transactions(
    limit: int = Query(50, ge=1, le=200, description="Max transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    sort: Literal["date_desc", "date_asc"] = Query("date_desc"),
    text: Optional[str] = Query(None, description="Filter by transaction text"),
    category: Optional[str] = Query(None, description="Filter by category"),
    account: Optional[str] = Query(None, description="Filter by account name"),
    date_from: Optional[date] = Query(
        None, description="Filter by minimum date (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter by maximum date (YYYY-MM-DD)"
    ),
):
    """
    Retrieves all transactions with their assigned category, with optional filtering.
    """
    transactions = get_all_transactions_db(
        limit=limit,
        offset=offset,
        sort=sort,
        text=text,
        account=account,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    total = count_transactions_db(
        text=text,
        account=account,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    return {
        "items": transactions,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
