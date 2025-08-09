# routers/accounts.py
from typing import List
from fastapi import APIRouter, HTTPException  # , Body
from ..models import Account  # , AccountUpdate
from ..crud import (
    get_account_by_name,
    create_or_update_account,
    get_all_accounts_db,
    # update_account_balance_db,
)

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Account, status_code=201)
def create_account(account: Account):
    """
    Adds a new account. If the account already exists, it is updated.
    """
    create_or_update_account(account)
    return account


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


# @router.patch("/{account_name}", response_model=Account)
# def update_account_balance(account_name: str, update_data: AccountUpdate = Body(...)):
#     """
#     Updates the balance for a specific account.
#     """
#     if not update_account_balance_db(account_name, update_data.balance):
#         raise HTTPException(status_code=404, detail="Account not found")

#     updated_account_data = get_account_by_name(account_name)
#     return Account(**dict(updated_account_data))
