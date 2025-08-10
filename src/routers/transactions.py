from typing import List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from ..models import Transaction, TransactionWithCategory
from ..crud import (
    get_transaction_by_id,
    create_transaction_db,
    get_all_transactions_db,
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


@router.get("/", response_model=List[TransactionWithCategory])
def get_all_transactions(
    text: Optional[str] = Query(None, description="Filter by transaction text"),
    account: Optional[str] = Query(None, description="Filter by account name"),
    min_date: Optional[date] = Query(
        None, description="Filter by minimum date (YYYY-MM-DD)"
    ),
    max_date: Optional[date] = Query(
        None, description="Filter by maximum date (YYYY-MM-DD)"
    ),
):
    """
    Retrieves all transactions with their assigned category, with optional filtering.
    """
    transactions = get_all_transactions_db(
        text=text, account=account, min_date=min_date, max_date=max_date
    )
    return [TransactionWithCategory(**dict(row)) for row in transactions]
