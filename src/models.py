from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Numeric,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), nullable=False
    )

    transactions: Mapped[List[Transaction]] = relationship(
        back_populates="account", cascade="all,delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )

    parent: Mapped[Optional[Category]] = relationship(
        remote_side="Category.id", backref="children"
    )


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(500))
    entity: Mapped[str] = mapped_column(String(500))
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )

    category: Mapped[Optional[Category]] = relationship()

    __table_args__ = (
        UniqueConstraint("text", "entity", name="uq_category_rules_text_entity"),
        Index("ix_category_rules_text", "text"),
        Index("ix_category_rules_entity", "entity"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(1000))
    entity: Mapped[str] = mapped_column(String(500))
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    date: Mapped[dt.date] = mapped_column(Date)
    reference: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    account: Mapped[Account] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_date", "date"),
        Index("ix_transactions_entity", "entity"),
        Index("ix_transactions_account_id", "account_id"),
    )
