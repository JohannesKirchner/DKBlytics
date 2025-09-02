"""
Pydantic models for data validation
"""

from __future__ import annotations
import datetime as dt
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# ---- Base Config ------------------------------------------------------------

BaseCfg = ConfigDict(
    from_attributes=True,  # allow ORM objects in responses
    extra="forbid",  # reject unexpected fields
    str_strip_whitespace=True,
)


class AppBaseModel(BaseModel):
    """Base for all API schemas with shared Pydantic config."""

    model_config = BaseCfg


# ---- Account ---------------------------------------------------------------


class AccountCreate(AppBaseModel):
    """Payload to create an account."""

    name: str = Field(..., max_length=255, description="Account name (unique).")
    balance: Decimal = Field(
        ..., ge=0, description="Initial/current balance for this account."
    )


class Account(AppBaseModel):
    """Account as returned by the API."""

    id: int = Field(..., description="Database ID.")
    name: str = Field(..., max_length=255, description="Account name (unique).")
    balance: Decimal = Field(..., ge=0, description="Current balance.")


# ---- Category --------------------------------------------------------------


class CategoryCreate(AppBaseModel):
    """Payload to create a transaction category."""

    name: str = Field(..., max_length=255, description="Category name.")
    parent_name: Optional[str] = Field(
        None,
        description="Direct parent category's name; omit for a root category.",
    )


class Category(AppBaseModel):
    """Category as returned by the API."""

    id: int = Field(..., description="Category ID.")
    name: str = Field(..., max_length=255, description="Category name.")
    parent_name: Optional[str] = Field(
        None, description="Direct parent category's name, if any."
    )


class CategoryTreeNode(AppBaseModel):
    """Node used by /categories/tree."""

    id: int = Field(..., description="Category ID.")
    name: str = Field(..., max_length=255, description="Category name.")
    children: List[CategoryTreeNode] = Field(
        default_factory=list, description="Nested child categories."
    )


# For recursive models, make sure annotations are resolved.
CategoryTreeNode.model_rebuild()


# ---- CategoryRule ----------------------------------------------------------


class CategoryRuleCreate(AppBaseModel):
    """
    Payload to create a category rule.

    Matching order (implemented in the service):
      1) exact match on (entity AND text)
      2) default match on (entity AND text IS NULL)
    """

    text: Optional[str] = Field(
        None,
        max_length=1000,
        description="Exact description text to match; use null for an entity-wide default.",
    )
    entity: str = Field(
        ..., max_length=500, description="Exact counterparty/entity to match."
    )
    category_name: str = Field(
        ..., description="Name of the category to assign when the rule matches."
    )


class CategoryRule(AppBaseModel):
    """Category rule as returned by the API."""

    id: int = Field(..., description="CategoryRule ID.")
    text: Optional[str] = Field(
        None,
        max_length=1000,
        description="Exact description text to match; null means entity-wide default.",
    )
    entity: str = Field(
        ..., max_length=500, description="Exact counterparty/entity to match."
    )
    category_name: str = Field(
        ..., description="Name of the category assigned by this rule."
    )


# ---- Transaction ------------------------------------------------------------


class TransactionCreate(AppBaseModel):
    """Payload to create a transaction."""

    text: str = Field(
        ..., max_length=1000, description="Transaction description text (free-form)."
    )
    entity: str = Field(
        ..., max_length=500, description="Counterparty/entity (exact string)."
    )
    account: str = Field(..., description="Account name this transaction belongs to.")
    amount: Decimal = Field(
        ...,
        description="Signed amount (negative = outflow, positive = inflow).",
    )
    date: dt.date = Field(..., description="Transaction date (YYYY-MM-DD).")
    reference: Optional[str] = Field(
        None, max_length=1000, description="Optional customer reference."
    )


class Transaction(AppBaseModel):
    """Transaction as returned by the API."""

    id: Optional[int] = Field(None, description="Transaction ID.")
    text: str = Field(..., max_length=1000, description="Transaction description text.")
    entity: str = Field(
        ..., max_length=500, description="Counterparty/entity (exact string)."
    )
    account: str = Field(..., description="Account name this transaction belongs to.")
    amount: Decimal = Field(
        ..., description="Signed amount (negative = outflow, positive = inflow)."
    )
    date: dt.date = Field(..., description="Transaction date (YYYY-MM-DD).")
    reference: Optional[str] = Field(
        None, max_length=1000, description="Optional customer reference."
    )
    fingerprint: Optional[str] = Field(
        None,
        max_length=64,
        pattern=r"^[0-9a-f]{40}$",
        description="40-character hex fingerprint used for de-duplication.",
    )


class TransactionWithCategory(Transaction):
    """Transaction including its resolved category (if any)."""

    category: Optional[str] = Field(None, description="Resolved category name, if any.")


class PaginatedTransactions(AppBaseModel):
    """Container for paginated transaction listings."""

    total: int = Field(..., ge=0, description="Total number of matching transactions.")
    limit: int = Field(..., gt=0, description="Page size (maximum number of items).")
    offset: int = Field(..., ge=0, description="Zero-based index of the first item.")
    items: List[TransactionWithCategory] = Field(
        ..., description="Transactions within the current page."
    )


class TransactionSummary(AppBaseModel):
    """Aggregate summary for transactions grouped by a key."""

    key: Optional[str] = Field(
        None,
        description="Grouping key (e.g., category name when grouped by category). None represents 'uncategorized'.",
    )
    amount_sum: Decimal = Field(
        ...,
        description="Sum of amounts in this group (negative = net outflow, positive = net inflow).",
    )
    count: int = Field(..., ge=0, description="Number of transactions in this group.")
