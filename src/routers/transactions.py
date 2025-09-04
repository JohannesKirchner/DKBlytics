from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    PaginatedTransactions,
    Transaction,
    TransactionCreate,
    TransactionSummary,
)
from ..services.transactions import (
    create_transaction_db,
    get_transaction_db,
    list_transactions_db,
    summarize_by_category_db,
)
from ..utils import NotFound, Conflict, BadRequest, Ambiguous


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
) -> Transaction:
    """
    Create a transaction.

    - Duplicate policy:
      * Allowed: duplicates when SAME (fingerprint, batch_hash)
      * Rejected (409): fingerprint exists with a DIFFERENT batch_hash
    - Category is resolved from rules for the response.
    """
    try:
        return create_transaction_db(db, payload)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=PaginatedTransactions)
def get_all_transactions(
    db: Session = Depends(get_db),
    limit: int = Query(50, gt=0, le=500, description="Page size."),
    offset: int = Query(0, ge=0, description="Zero-based start index."),
    sort_by: str = Query(
        "date_desc",
        description="Sort order.",
        pattern="^(date_desc|date_asc|amount_desc|amount_asc)$",
    ),
    date_from: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    date_to: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    account_id: Optional[str] = Query(None, description="Filter by account public_id."),
    q: Optional[str] = Query(
        None, description="Case-insensitive search in entity/text/reference."
    ),
) -> PaginatedTransactions:
    """List transactions with pagination, sorting, and filters."""
    try:
        return list_transactions_db(
            db,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            date_from=date_from,
            date_to=date_to,
            account_id=account_id,
            q=q,
        )
    except BadRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/summary", response_model=List[TransactionSummary])
def summarize_transactions_by_category(
    db: Session = Depends(get_db),
    scope_name: Optional[str] = Query(
        None,
        description=(
            "Parent category name whose subtree is the scope. " "Omit for global roots."
        ),
    ),
    depth: int = Query(
        1,
        ge=1,
        description=(
            "Depth within the scope to define the groups. "
            "1 = direct children; 2 = grandchildren; etc."
        ),
    ),
    date_from: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    date_to: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    account_id: Optional[str] = Query(None, description="Filter by account public_id."),
    q: Optional[str] = Query(
        None, description="Case-insensitive search in entity/text/reference."
    ),
) -> List[TransactionSummary]:
    """
    Summarize transactions **by category nodes** at a given depth within an optional scope.

    Examples:
    - `scope_name=None, depth=1` ⇒ group by root categories.
    - `scope_name=\"Expenses\", depth=1` ⇒ group by direct children of “Expenses”.
    - `scope_name=\"Expenses\", depth=2` ⇒ group by grandchildren of “Expenses”.

    Notes:
    - If a resolved transaction category is shallower than the requested depth within the scope,
      it is grouped under its deepest available ancestor (not dropped).
    - You can filter via `account`, `date_from`, `date_to`, and `q`. There is **no** separate “group by account”.
    """
    try:
        return summarize_by_category_db(
            db,
            scope_name=scope_name,
            depth=depth,
            date_from=date_from,
            date_to=date_to,
            account_id=account_id,
            q=q,
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Ambiguous as e:
        # Scope category name exists under multiple parents
        raise HTTPException(status_code=409, detail=str(e))
    except BadRequest as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tx_id}", response_model=Transaction)
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
) -> Transaction:
    """Retrieve a single transaction."""
    try:
        return get_transaction_db(db, tx_id)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
