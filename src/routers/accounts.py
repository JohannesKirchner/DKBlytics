from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..schemas import Account, AccountCreate
from ..database import get_db
from ..services.accounts import (
    get_account_by_name,
    create_or_update_account,
    get_all_accounts_db,
)

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db)) -> Account:
    """
    Adds a new account. If the account already exists, it is updated.
    """
    return create_or_update_account(db, account)


@router.get("/{account_name}", response_model=Account)
def get_account(account_name: str, db: Session = Depends(get_db)) -> Account:
    """
    Retrieves a specific account.
    """
    account = get_account_by_name(db, account_name)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    return account


@router.get("/", response_model=List[Account])
def get_all_accounts(db: Session = Depends(get_db)) -> List[Account]:
    """
    Retrieves all accounts.
    """
    accounts = get_all_accounts_db(db)

    return accounts
