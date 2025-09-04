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
    """Payload to create or update an account (IBAN never leaves the API)."""

    name: str = Field(
        ..., max_length=255, description="Human-friendly account name (not unique)."
    )
    holder_name: str = Field(
        ...,
        max_length=255,
        description="Account holder's full name as provided by the bank.",
    )
    iban_plain: str = Field(
        ...,
        max_length=34,
        description="Raw IBAN. Used server-side only to compute a keyed digest; never returned.",
    )
    balance: Decimal = Field(..., ge=0, description="Current balance for this account.")


class Account(AppBaseModel):
    """Account as returned by the API (IBAN is not exposed)."""

    id: int = Field(..., description="Database row ID.")
    public_id: str = Field(
        ..., description="Opaque, stable identifier to reference this account in APIs."
    )
    name: str = Field(..., max_length=255, description="Human-friendly account name.")
    holder_name: str = Field(
        ..., max_length=255, description="Account holder's full name."
    )
    iban_last4: Optional[str] = Field(
        None,
        description="Last 4 characters of the IBAN for display; may be null if not available.",
    )
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
        ...,
        max_length=1000,
        description="Transaction description text from the statement.",
    )
    entity: str = Field(
        ...,
        max_length=255,
        description="Counterparty/entity name as extracted from the statement.",
    )
    account_id: str = Field(
        ..., description="Account public_id this transaction belongs to."
    )
    amount: Decimal = Field(
        ..., description="Signed amount (negative = outflow, positive = inflow)."
    )
    date: dt.date = Field(..., description="Booking date in YYYY-MM-DD format.")
    reference: Optional[str] = Field(
        None, max_length=1000, description="Optional customer reference or memo."
    )
    batch_hash: Optional[str] = Field(
        None,
        max_length=40,
        description="Optional batch identifier. Duplicates are allowed within the same batch; "
        "cross-batch duplicate fingerprints are rejected.",
    )


class Transaction(AppBaseModel):
    """Transaction as returned by the API."""

    id: Optional[int] = Field(None, description="Transaction ID.")
    text: str = Field(..., max_length=1000, description="Transaction description text.")
    entity: str = Field(..., max_length=500, description="Counterparty/entity name.")
    account_id: str = Field(
        ..., description="Account public_id this transaction belongs to."
    )
    account_name: str = Field(
        ..., max_length=255, description="Human-friendly account name."
    )
    amount: Decimal = Field(
        ..., description="Signed amount (negative = outflow, positive = inflow)."
    )
    date: dt.date = Field(..., description="Booking date in YYYY-MM-DD format.")
    reference: Optional[str] = Field(
        None, max_length=1000, description="Optional customer reference."
    )
    fingerprint: Optional[str] = Field(
        None,
        max_length=40,
        pattern=r"^[0-9a-f]{40}$",
        description="40-char hex fingerprint for de-duplication.",
    )
    batch_hash: Optional[str] = Field(
        None, max_length=40, description="Batch identifier, if provided."
    )
    category: Optional[str] = Field(
        None, description="Resolved category name based on rules, if any."
    )


class PaginatedTransactions(AppBaseModel):
    """Container for paginated transaction listings."""

    total: int = Field(..., ge=0, description="Total number of matching transactions.")
    limit: int = Field(..., gt=0, description="Page size (maximum number of items).")
    offset: int = Field(..., ge=0, description="Zero-based index of the first item.")
    items: List[Transaction] = Field(
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
    transactions: List["Transaction"] = Field(
        default_factory=list,
        description="All transactions that contributed to this group's amount.",
    )
