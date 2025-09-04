from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session

from ..schemas import Account, AccountCreate
from ..database import get_db
from ..services.accounts import (
    create_account_db,
    update_account_db,
    get_all_accounts_db,
    get_account_by_public_id_db,
)
from ..utils import Conflict, NotFound, BadRequest

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    """
    Create a new account.

    Returns 201 on success.
    Returns 409 if an account with the same name already exists.
    """
    try:
        return create_account_db(db, payload)
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/{public_id}", response_model=Account)
def update_account(
    public_id: str,
    payload: AccountCreate,
    db: Session = Depends(get_db),
) -> Account:
    """
    Update an existing account's balance.

    - The body `name` must match the path `public_id`.
    - Returns 404 if the account does not exist.
    - Returns 400 if the names do not match.
    - Returns 409 if the IBAN is already taken by another account.
    """
    try:
        return update_account_db(db, public_id=public_id, payload=payload)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{public_id}", response_model=Account)
def get_account(public_id: str, db: Session = Depends(get_db)) -> Account:
    """
    Retrieve a specific account by public ID.
    """
    try:
        return get_account_by_public_id_db(db, public_id)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=List[Account])
def get_all_accounts(
    db: Session = Depends(get_db),
    name: Optional[str] = Query(None, description="Filter by account name (exact)."),
    holder: Optional[str] = Query(None, description="Filter by holder_name (exact)."),
) -> List[Account]:
    """
    Retrieve all accounts (sorted by name).
    """
    return get_all_accounts_db(db, name=name, holder=holder)
