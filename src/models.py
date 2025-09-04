from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,  # unique=True,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), nullable=False
    )

    transactions: Mapped[List[Transaction]] = relationship(
        back_populates="account", cascade="all,delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )

    parent: Mapped[Optional[Category]] = relationship(
        "Category",
        remote_side=[id],
        foreign_keys=[parent_id],
        backref="children",
    )

    __table_args__ = (
        # Unique among siblings (same parent)
        UniqueConstraint("parent_id", "name", name="uq_categories_parent_name"),
    )


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # text is optional; when NULL this acts as the default rule for the entity
    text: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    # entity is required (no text-only rules)
    entity: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category: Mapped[Category] = relationship("Category", backref="rules")

    __table_args__ = (
        # Disallow empty entity and enforce that at least entity is present.
        # CheckConstraint(
        #    "entity IS NOT NULL AND entity <> '' AND (text IS NULL OR text <> '')",
        #    name="ck_category_rules_entity_and_text_not_both_empty",
        # ),
        # One exact rule per (entity, text) pair
        UniqueConstraint("entity", "text", name="uq_category_rules_entity_text"),
        # One default rule per entity (when text IS NULL)
        # Index(
        #    "uq_category_rules_entity_default",
        #    "entity",
        #    unique=True,
        #    sqlite_where="text IS NULL",
        # ),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    account: Mapped[Account] = relationship("Account", back_populates="transactions")

    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Free-form transaction text and counterparty/payee
    text: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, index=True)
    entity: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    reference: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # De-duplication
    fingerprint: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    batch_hash: Mapped[Optional[str]] = mapped_column(String(40), index=True)
