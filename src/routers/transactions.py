from typing import Optional, Literal, List
from datetime import date
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import (
    Transaction,
    TransactionCreate,
    PaginatedTransactions,
    TransactionSummary,
)
from ..services.transactions import (
    get_transaction_by_id,
    create_transaction_db,
    get_all_transactions_db,
    count_transactions_db,
    get_transactions_summary,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Transaction, status_code=201)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """
    Adds a new transaction to the database.
    """
    db_transaction = create_transaction_db(db, transaction)
    return db_transaction


@router.get("/", response_model=PaginatedTransactions)
def get_all_transactions(
    limit: int = Query(50, ge=1, le=200, description="Max transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    sort_by: Literal["date_desc", "date_asc"] = Query("date_desc"),
    text: Optional[str] = Query(None, description="Filter by transaction text"),
    entity: Optional[str] = Query(None, description="Filter by transaction entity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    account: Optional[str] = Query(None, description="Filter by account name"),
    date_from: Optional[date] = Query(
        None, description="Filter by minimum date (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter by maximum date (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieves all transactions with their assigned category, with optional filtering.
    """
    transactions = get_all_transactions_db(
        db,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        text=text,
        entity=entity,
        account=account,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    total = count_transactions_db(
        db,
        text=text,
        entity=entity,
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


@router.get(
    "/summary",
    response_model=List[TransactionSummary],
    summary="Aggregate totals per category or per month",
    description="Returns total sum and count of transactions grouped by category or by month (YYYY-MM).",
)
def transactions_summary(
    group_by_category: bool = Query(True, description="Aggregation dimension"),
    text: Optional[str] = Query(None, description="Search in text/entity"),
    account: Optional[str] = Query(None, description="Filter by account name"),
    date_from: Optional[date] = Query(
        None, description="Filter by minimum date (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter by maximum date (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
):
    """
    Response shape:
    [
        {"key": "Groceries", "amount_sum": "123.45", "count": 7},
        {"key": "Rent", "amount_sum": "900.00", "count": 1}
    ]
    """
    return get_transactions_summary(
        db,
        group_by_category=group_by_category,
        text=text,
        account=account,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single transaction by its ID.
    """
    transaction_data = get_transaction_by_id(db, transaction_id)
    if transaction_data:
        return Transaction(**dict(transaction_data))
    raise HTTPException(status_code=404, detail="Transaction not found")
