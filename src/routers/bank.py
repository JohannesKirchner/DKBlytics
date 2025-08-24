from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from ..database import get_db
from ..services.bank import get_new_transactions


router = APIRouter(
    tags=["Bank Integration"],
    responses={404: {"description": "Not found"}},
)


@router.post("/update_from_bank/")
def update_from_bank(db: Session = Depends(get_db)):
    """
    Connects to a bank API, fetches new transactions, adds them to the database,
    and creates placeholder categories for new (text, entity) pairs.
    """
    new_transactions = get_new_transactions(db)

    return {
        "message": f"Successfully updated transactions: {dict(new_transactions)}. New category rules may have been added."
    }
