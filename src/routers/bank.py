import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from fastapi import APIRouter
from dkb_robo import DKBRobo
from datetime import datetime
from ..crud import create_transaction_db, create_or_update_account
from ..models import Account, Transaction
from collections import defaultdict


load_dotenv("dkb_credentials.env")

router = APIRouter(
    tags=["Bank Integration"],
    responses={404: {"description": "Not found"}},
)


def fetch_bank_data():
    """
    Simulates fetching data from a hypothetical bank API.

    """
    # Placeholder for transactions from your bank
    with DKBRobo(
        dkb_user=os.getenv("DKB_USERNAME"),
        dkb_password=os.getenv("DKB_PASSWORD"),
        chip_tan=False,
        mfa_device=os.getenv("DKB_MFA_DEVICE"),
        debug=False,
        unfiltered=False,
    ) as dkb:
        accounts = list(dkb.account_dic.values())
        account_transactions = []
        for account in accounts:
            account_transactions.append(
                dkb.get_transactions(
                    account["transactions"],
                    account["type"],
                    "01.01.2023",
                    datetime.now().strftime("%d.%m.%Y"),
                )
            )

    return accounts, account_transactions


@router.post("/update_from_bank/")
def update_from_bank():
    """
    Connects to a bank API, fetches new transactions,
    adds them to the database (without duplicates), and updates the balance.
    """
    accounts, account_transactions = fetch_bank_data()

    new_transactions = defaultdict(int)
    for account, transactions in zip(accounts, account_transactions):
        try:
            create_or_update_account(
                Account(name=account["name"], balance=account["amount"])
            )
        except KeyError:
            print(f"Account {account["name"]} does not have a balance field.")
            continue

        for transaction in transactions:
            if create_transaction_db(
                Transaction(
                    text=transaction["text"],
                    entity=transaction["peer"],
                    account=account["name"],
                    amount=transaction["amount"],
                    date=transaction["date"],
                    reference=transaction["customerreference"],
                )
            ):
                new_transactions[account["name"]] += 1

    return {
        "message": f"Successfully updated transaction {new_transactions} from bank API.",
    }
