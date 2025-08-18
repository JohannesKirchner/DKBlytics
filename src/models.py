import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# --- Pydantic Models for Data Validation ---


class Transaction(BaseModel):
    """
    Pydantic model for a transaction.
    """

    text: str = Field(..., description="The description text of the transaction.")
    entity: str = Field(
        ..., description="The entity receiving or issuing the transaction."
    )
    account: str = Field(..., description="The account the transaction belongs to.")
    amount: float = Field(..., description="The transaction amount.")
    date: datetime.date = Field(
        ..., description="The date of the transaction in YYYY-MM-DD format."
    )
    reference: str | None = Field(..., description="Customer reference")
    fingerprint: Optional[str] = Field(
        None, description="Unique fingerprint for each transaction"
    )
    transaction_id: Optional[int] = Field(
        None, description="The unique ID of the transaction."
    )


class TransactionWithCategory(Transaction):
    """
    Pydantic model for a transaction that includes its category.
    """

    category: Optional[str] = Field(
        None, description="The assigned category for the transaction."
    )


class PaginatedTransactions(BaseModel):
    items: List[TransactionWithCategory] = Field(
        ..., description="List of all relevant transactions whithin limits."
    )
    total: int = Field(..., description="Total count of all relevant transactions.")
    limit: int = Field(..., description="Limit of all displayed transactions.")
    offset: int = Field(..., description="Offset of the first transaction.")


class Account(BaseModel):
    """
    Pydantic model for an account.
    """

    name: str = Field(..., description="The name of the account.")
    balance: float = Field(..., ge=0, description="The current balance of the account.")


class Category(BaseModel):
    """
    Pydantic model for a transaction category.
    """

    text: str = Field(..., description="The text from the transaction description.")
    entity: str = Field(..., description="The entity from the transaction.")
    category: Optional[str] = Field(None, description="The assigned category.")


class CategoryUpdate(BaseModel):
    """
    Pydantic model for updating a category.
    """

    category: str = Field(..., description="The new category name.")
