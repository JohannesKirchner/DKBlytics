from __future__ import annotations

import datetime as dt
from enum import Enum
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..models import Account as AccountORM
from ..schemas import BalancePoint, SurplusPoint
from ..utils import BadRequest, NotFound

DEFAULT_LOOKBACK_DAYS = 90
FISCAL_MONTH_START_DAY = 15  # configurable anchor for fiscal months


class Granularity(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    fiscal_monthly = "fiscal_monthly"


def get_balance_series_db(
    db: Session,
    *,
    account_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    granularity: Union[str, Granularity] = Granularity.daily,
) -> List[BalancePoint]:
    start_date, end_date = _resolve_date_range(date_from, date_to)
    granularity = _normalize_granularity(granularity)

    rows = _load_rows(db, account_id, start_date, end_date)
    points: List[BalancePoint] = [
        BalancePoint(date=date, balance=balance)
        for date, balance in _collapse_balance(rows, granularity)
    ]
    return points


def get_surplus_series_db(
    db: Session,
    *,
    account_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    granularity: Union[str, Granularity] = Granularity.daily,
) -> List[SurplusPoint]:
    start_date, end_date = _resolve_date_range(date_from, date_to)
    granularity = _normalize_granularity(granularity)

    rows = _load_rows(db, account_id, start_date, end_date)
    points: List[SurplusPoint] = [
        SurplusPoint(date=date, delta=delta)
        for date, delta in _collapse_surplus(rows, granularity)
    ]
    return points


# ---------------------------------------------------------------------------
# Row loading
# ---------------------------------------------------------------------------


class _DailyRow:
    __slots__ = ("date", "delta", "closing_balance")

    def __init__(self, *, date: dt.date, delta: Decimal, closing_balance: Decimal) -> None:
        self.date = date
        self.delta = delta
        self.closing_balance = closing_balance


def _load_rows(
    db: Session,
    account_id: Optional[str],
    start_date: dt.date,
    end_date: dt.date,
) -> Sequence[_DailyRow]:
    if account_id:
        account = _require_account(db, account_id)
        return _fetch_daily_rows_for_account(
            db,
            account_id=account.public_id,
            balance=account.balance,
            start_date=start_date,
            end_date=end_date,
        )

    if not _has_accounts(db):
        return []

    return _fetch_daily_rows_combined(db, start_date=start_date, end_date=end_date)


def _fetch_daily_rows_for_account(
    db: Session,
    *,
    account_id: str,
    balance: Decimal,
    start_date: dt.date,
    end_date: dt.date,
) -> List[_DailyRow]:
    query = text(
        """
        WITH RECURSIVE date_grid(day) AS (
            SELECT :start_date
            UNION ALL
            SELECT date(day, '+1 day') FROM date_grid WHERE day < :end_date
        ),
        future_tx AS (
            SELECT COALESCE(SUM(amount), 0) AS future_sum
            FROM transactions
            WHERE account_id = :account_id AND date > :end_date
        ),
        base_balance AS (
            SELECT CAST(:balance AS NUMERIC) - future_tx.future_sum AS base_balance FROM future_tx
        ),
        daily_tx AS (
            SELECT date, SUM(amount) AS delta
            FROM transactions
            WHERE account_id = :account_id AND date BETWEEN :start_date AND :end_date
            GROUP BY date
        ),
        series AS (
            SELECT
                dg.day AS date,
                COALESCE(dt.delta, 0) AS delta,
                base_balance.base_balance AS base_balance
            FROM date_grid dg
            CROSS JOIN base_balance
            LEFT JOIN daily_tx dt ON dt.date = dg.day
        )
        SELECT
            date,
            delta,
            base_balance - COALESCE(
                SUM(delta) OVER (ORDER BY date DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),
                0
            ) AS closing_balance
        FROM series
        ORDER BY date ASC
        """
    )
    rows = db.execute(
        query,
        {
            "account_id": account_id,
            "balance": str(balance),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    ).mappings()

    return [
        _DailyRow(
            date=_ensure_date(r["date"]),
            delta=_to_decimal(r["delta"]),
            closing_balance=_to_decimal(r["closing_balance"]),
        )
        for r in rows
    ]


def _fetch_daily_rows_combined(
    db: Session,
    *,
    start_date: dt.date,
    end_date: dt.date,
) -> List[_DailyRow]:
    query = text(
        """
        WITH RECURSIVE date_grid(day) AS (
            SELECT :start_date
            UNION ALL
            SELECT date(day, '+1 day') FROM date_grid WHERE day < :end_date
        ),
        future_tx AS (
            SELECT account_id, SUM(amount) AS future_sum
            FROM transactions
            WHERE date > :end_date
            GROUP BY account_id
        ),
        base_balance AS (
            SELECT COALESCE(SUM(a.balance - COALESCE(f.future_sum, 0)), 0) AS base_balance
            FROM accounts a
            LEFT JOIN future_tx f ON f.account_id = a.public_id
        ),
        daily_tx AS (
            SELECT
                date,
                SUM(amount) AS delta
            FROM transactions
            WHERE date BETWEEN :start_date AND :end_date
            GROUP BY date
        ),
        series AS (
            SELECT
                dg.day AS date,
                COALESCE(dt.delta, 0) AS delta,
                base_balance.base_balance AS base_balance
            FROM date_grid dg
            CROSS JOIN base_balance
            LEFT JOIN daily_tx dt ON dt.date = dg.day
        )
        SELECT
            date,
            delta,
            base_balance - COALESCE(
                SUM(delta) OVER (ORDER BY date DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),
                0
            ) AS closing_balance
        FROM series
        ORDER BY date ASC
        """
    )
    rows = db.execute(
        query,
        {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    ).mappings()

    return [
        _DailyRow(
            date=_ensure_date(r["date"]),
            delta=_to_decimal(r["delta"]),
            closing_balance=_to_decimal(r["closing_balance"]),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------


def _collapse_balance(
    rows: Sequence[_DailyRow], granularity: Granularity
) -> Iterable[Tuple[dt.date, Decimal]]:
    if granularity is Granularity.daily:
        for row in rows:
            yield row.date, row.closing_balance
        return

    current_bucket = None
    last_row: Optional[_DailyRow] = None
    for row in rows:
        bucket = _bucket_id(row.date, granularity)
        if current_bucket is None:
            current_bucket = bucket
        elif bucket != current_bucket and last_row is not None:
            yield last_row.date, last_row.closing_balance
            current_bucket = bucket
        last_row = row
    if last_row is not None:
        yield last_row.date, last_row.closing_balance


def _collapse_surplus(
    rows: Sequence[_DailyRow], granularity: Granularity
) -> Iterable[Tuple[dt.date, Decimal]]:
    if granularity is Granularity.daily:
        for row in rows:
            yield row.date, row.delta
        return

    current_bucket = None
    bucket_delta = Decimal("0")
    last_date: Optional[dt.date] = None
    for row in rows:
        bucket = _bucket_id(row.date, granularity)
        if current_bucket is None:
            current_bucket = bucket
        elif bucket != current_bucket and last_date is not None:
            yield last_date, bucket_delta
            current_bucket = bucket
            bucket_delta = Decimal("0")
        bucket_delta += row.delta
        last_date = row.date
    if last_date is not None:
        yield last_date, bucket_delta


def _bucket_id(day: dt.date, granularity: Granularity) -> Tuple[int, int]:
    if granularity is Granularity.weekly:
        iso = day.isocalendar()
        return (iso.year, iso.week)
    if granularity is Granularity.monthly:
        return (day.year, day.month)
    if granularity is Granularity.fiscal_monthly:
        start = _fiscal_month_start(day)
        return (start.year, start.month)
    if granularity is Granularity.yearly:
        return (day.year, 0)
    return (day.year, day.timetuple().tm_yday)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _normalize_granularity(value: Union[str, Granularity]) -> Granularity:
    if isinstance(value, Granularity):
        return value
    normalized = (value or Granularity.daily.value).lower()
    try:
        return Granularity(normalized)
    except ValueError as exc:
        raise BadRequest(
            "granularity must be one of daily, weekly, monthly, fiscal_monthly, yearly"
        ) from exc


def _fiscal_month_start(day: dt.date) -> dt.date:
    anchor = FISCAL_MONTH_START_DAY
    if day.day >= anchor:
        return day.replace(day=anchor)
    prev_month_last = day.replace(day=1) - dt.timedelta(days=1)
    return prev_month_last.replace(day=anchor)


def _resolve_date_range(
    date_from: Optional[str],
    date_to: Optional[str],
) -> Tuple[dt.date, dt.date]:
    today = dt.date.today()
    end = _parse_date(date_to, field="date_to") if date_to else today
    if date_from:
        start = _parse_date(date_from, field="date_from")
    else:
        start = end - dt.timedelta(days=DEFAULT_LOOKBACK_DAYS - 1)
    if start > end:
        raise BadRequest("date_from must be on or before date_to.")
    return start, end


def _parse_date(value: str, *, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise BadRequest(f"Invalid {field}: expected YYYY-MM-DD.") from exc


def _require_account(db: Session, account_id: str) -> AccountORM:
    account = db.scalar(select(AccountORM).where(AccountORM.public_id == account_id))
    if not account:
        raise NotFound("Account not found.")
    return account


def _has_accounts(db: Session) -> bool:
    return db.scalar(select(AccountORM).limit(1)) is not None


def _ensure_date(value) -> dt.date:
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        return dt.date.fromisoformat(value)
    raise TypeError(f"Unsupported date value: {value!r}")


TWOPLACES = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        quantized = value.quantize(TWOPLACES)
    else:
        if value is None:
            quantized = Decimal("0")
        else:
            quantized = Decimal(str(value))
        quantized = quantized.quantize(TWOPLACES)
    return quantized
