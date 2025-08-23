from typing import List
from fastapi import APIRouter, HTTPException
from ..models import Account
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


@router.post("/", status_code=201)
def create_account(account: Account):
    """
    Adds a new account. If the account already exists, it is updated.
    """
    old_account = get_account_by_name(account.name)
    account_id = create_or_update_account(account)
    if old_account.name == account.name:
        message = f"Successfully updated Account {old_account.name} (ID: {account_id})."
    else:
        message = f"Created new Account {account.name} (ID: {account_id})."

    return {"message": message}


@router.get("/{account_name}", response_model=Account)
def get_account(account_name: str):
    """
    Retrieves a specific account.
    """
    account_data = get_account_by_name(account_name)
    if account_data:
        return Account(**dict(account_data))

    raise HTTPException(status_code=404, detail="Account not found")


@router.get("/", response_model=List[Account])
def get_all_accounts():
    """
    Retrieves all accounts.
    """
    accounts = get_all_accounts_db()

    return [Account(**dict(row)) for row in accounts]
