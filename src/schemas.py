"""
Pydantic models for data validation
"""

import datetime as dt
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# ---- Base Config ------------------------------------------------------------

BaseCfg = ConfigDict(
    from_attributes=True,  # allow ORM objects in responses
    # extra="forbid",  # reject unexpected fields
    str_strip_whitespace=True,
)


# ---- Account ---------------------------------------------------------------


class AccountCreate(BaseModel):
    """
    Pydantic model for an account.
    """

    model_config = BaseCfg

    name: str = Field(..., max_length=255, description="The name of the account.")
    balance: Decimal = Field(
        ..., ge=0, description="The current balance of the account."
    )


class Account(BaseModel):
    """
    Pydantic model for an account.
    """

    model_config = BaseCfg

    id: int = Field(..., description="Database ID")
    name: str = Field(..., max_length=255, description="The name of the account.")
    balance: Decimal = Field(
        ..., ge=0, description="The current balance of the account."
    )


# ---- Category --------------------------------------------------------------


class CategoryCreate(BaseModel):
    """
    Pydantic model for a transaction category.
    """

    model_config = BaseCfg

    name: str = Field(..., max_length=255, description="The name of the category.")
    parent_name: Optional[str] = Field(None, description="Parent category name.")


class Category(BaseModel):
    """
    Pydantic model for a transaction category.
    """

    model_config = BaseCfg

    id: int = Field(..., description="The assigned category ID.")
    name: str = Field(..., max_length=255, description="The name of the category.")
    parent_name: Optional[str] = Field(None, description="Parent category name.")


# ---- CategoryRule ----------------------------------------------------------


class CategoryRuleCreate(BaseModel):
    """
    Pydantic model for a transaction category rule.
    """

    model_config = BaseCfg

    text: Optional[str] = Field(
        None, max_length=1000, description="The text from the transaction description."
    )
    entity: str = Field(
        ..., max_length=500, description="The entity from the transaction."
    )
    category_name: str = Field(..., description="The assigned category id.")


class CategoryRule(BaseModel):
    """
    Pydantic model for a transaction category rule.
    """

    model_config = BaseCfg

    id: int = Field(..., description="The assigned category ID.")
    text: Optional[str] = Field(
        None, max_length=1000, description="The text from the transaction description."
    )
    entity: str = Field(
        ..., max_length=500, description="The entity from the transaction."
    )
    category_name: str = Field(..., description="The assigned category id.")


# ---- Transaction ------------------------------------------------------------


class TransactionCreate(BaseModel):
    """
    Pydantic model for a transaction.
    """

    model_config = BaseCfg

    text: str = Field(
        ..., max_length=1000, description="The description text of the transaction."
    )
    entity: str = Field(
        ...,
        max_length=500,
        description="The entity receiving or issuing the transaction.",
    )
    account: str = Field(..., description="The account the transaction belongs to.")
    amount: Decimal = Field(..., description="The transaction amount.")
    date: dt.date = Field(
        ..., description="The date of the transaction in YYYY-MM-DD format."
    )
    reference: Optional[str] = Field(
        None, max_length=1000, description="Customer reference"
    )


class Transaction(BaseModel):
    """
    Pydantic model for a transaction.
    """

    model_config = BaseCfg

    id: Optional[int] = Field(None, description="The unique ID of the transaction.")
    text: str = Field(
        ..., max_length=1000, description="The description text of the transaction."
    )
    entity: str = Field(
        ...,
        max_length=500,
        description="The entity receiving or issuing the transaction.",
    )
    account: str = Field(..., description="The account the transaction belongs to.")
    amount: Decimal = Field(..., description="The transaction amount.")
    date: dt.date = Field(
        ..., description="The date of the transaction in YYYY-MM-DD format."
    )
    reference: Optional[str] = Field(
        None, max_length=1000, description="Customer reference"
    )
    fingerprint: Optional[str] = Field(
        None,
        max_length=40,
        pattern=r"^[0-9a-f]{40}$",
        description="40-character hex fingerprint.",
    )


class TransactionWithCategory(Transaction):
    """
    Pydantic model for a transaction that includes its category.
    """

    category: Optional[str] = Field(
        None, description="The assigned category for the transaction."
    )


class PaginatedTransactions(BaseModel):
    model_config = BaseCfg

    items: List[TransactionWithCategory] = Field(
        ..., description="List of all relevant transactions whithin limits."
    )
    total: int = Field(
        ..., ge=0, description="Total count of all relevant transactions."
    )
    limit: int = Field(..., gt=0, description="Limit of all displayed transactions.")
    offset: int = Field(..., ge=0, description="Offset of the first transaction.")


class TransactionSummary(BaseModel):
    key: Optional[str] = Field(
        None,
        description="Grouping key: category name when group_by=category (None means uncategorized), ",
    )
    amount_sum: Decimal = Field(
        ...,
        description="Sum of transaction amounts in this group. Negative = net outflow, positive = net inflow.",
    )
    count: int = Field(
        ..., ge=0, description="Number of transactions contributing to this group."
    )
