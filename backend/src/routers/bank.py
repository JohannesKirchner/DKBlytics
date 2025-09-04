from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.bank import get_new_transactions, ExternalServiceError

router = APIRouter(
    prefix="/bank",
    tags=["Bank Integration"],
    responses={404: {"description": "Not found"}},
)


@router.post("/update_from_bank", status_code=status.HTTP_200_OK)
def update_from_bank(db: Session = Depends(get_db)):
    """
    Connect to the bank API, fetch new transactions, insert them,
    and update account balances.

    Returns a mapping of account name -> number of inserted transactions for this run.
    """
    try:
        new_transactions = get_new_transactions(db)
    except ExternalServiceError as e:
        # Upstream banking API is failing/unavailable
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return {
        "message": "Bank update completed.",
        "inserted": new_transactions,
    }
