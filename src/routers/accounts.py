from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..schemas import Account, AccountCreate
from ..database import get_db
from ..services.accounts import (
    create_account_db,
    update_account_db,
    get_all_accounts_db,
    get_account_by_name_db,
)
from ..services.utils import Conflict, NotFound, BadRequest

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db)) -> Account:
    """
    Create a new account.

    Returns 201 on success.
    Returns 409 if an account with the same name already exists.
    """
    try:
        return create_account_db(db, account)
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/{account_name}", response_model=Account)
def update_account(
    account_name: str,
    account: AccountCreate,
    db: Session = Depends(get_db),
) -> Account:
    """
    Update an existing account's balance.

    - The body `name` must match the path `account_name`.
    - Returns 404 if the account does not exist.
    - Returns 400 if the names do not match.
    """
    try:
        return update_account_db(db, account_name, account)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{account_name}", response_model=Account)
def get_account(account_name: str, db: Session = Depends(get_db)) -> Account:
    """
    Retrieve a specific account by name.
    """
    try:
        return get_account_by_name_db(db, account_name)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=List[Account])
def get_all_accounts(db: Session = Depends(get_db)) -> List[Account]:
    """
    Retrieve all accounts (sorted by name).
    """
    return get_all_accounts_db(db)
