from typing import List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Body, Query
from ..models import Transaction  # , TransactionUpdate  # , TransactionWithCategory,
from ..crud import (
    get_transaction_by_id,
    create_transaction_db,
    get_all_transactions_db,
    # update_transaction_db,
    # get_transactions_with_categories_db,
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


@router.get("/", response_model=List[Transaction])
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
    Retrieves all transactions with optional filtering.
    """
    transactions = get_all_transactions_db(
        text=text, account=account, min_date=min_date, max_date=max_date
    )
    return [Transaction(**dict(row)) for row in transactions]


# @router.get("/with_category", response_model=List[TransactionWithCategory])
# def get_transactions_with_categories():
#     """
#     Retrieves all transactions with their assigned category.
#     """
#     transactions = get_transactions_with_categories_db()
#     return [TransactionWithCategory(**dict(row)) for row in transactions]


# @router.patch("/{transaction_id}", response_model=Transaction)
# def update_transaction(transaction_id: int, update_data: TransactionUpdate):
#     """
#     Updates an existing transaction.
#     """
#     update_data_dict = update_data.dict(exclude_unset=True)
#     if not update_transaction_db(transaction_id, update_data_dict):
#         raise HTTPException(status_code=404, detail="Transaction not found")

#     updated_transaction_data = get_transaction_by_id(transaction_id)
#     return Transaction(**dict(updated_transaction_data))


# @router.patch("/{transaction_id}", response_model=Transaction)
# def update_transaction_type(
#     transaction_id: int, update_data: TransactionUpdate = Body(...)
# ):
#     """
#     Updates the type of an existing transaction.
#     """
#     if not update_transaction_type_db(transaction_id, update_data.type):
#         raise HTTPException(status_code=404, detail="Transaction not found")

#     updated_transaction_data = get_transaction_by_id(transaction_id)
#     return Transaction(**dict(updated_transaction_data))
