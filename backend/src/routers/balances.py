from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import BalancePoint, SurplusPoint
from ..services.balances import Granularity, get_surplus_series_db, get_balance_series_db
from ..utils import BadRequest, NotFound

router = APIRouter(
    prefix="/balances",
    tags=["Balances"],
    responses={404: {"description": "Not found"}},
)


@router.get("/series", response_model=List[BalancePoint])
def get_balance_series(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Query(None, description="Optional account filter."),
    date_from: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    date_to: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    granularity: Granularity = Query(
        Granularity.daily,
        description=(
            "Bucket size for the returned series (daily/weekly/monthly/"
            "fiscal_monthly/yearly)."
        ),
    ),
) -> List[BalancePoint]:
    """Return a lightweight series with `date` + `balance` at the chosen granularity."""

    try:
        return get_balance_series_db(
            db,
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            granularity=granularity,
        )
    except NotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BadRequest as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/surplus", response_model=List[SurplusPoint])
def get_surplus_series(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Query(None, description="Optional account filter."),
    date_from: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    date_to: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    granularity: Granularity = Query(
        Granularity.daily,
        description=(
            "Bucket size for the returned surplus buckets (daily/weekly/monthly/"
            "fiscal_monthly/yearly)."
        ),
    ),
) -> List[SurplusPoint]:
    """Return aggregated deltas ("surplus") for the given range."""

    try:
        return get_surplus_series_db(
            db,
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            granularity=granularity,
        )
    except NotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BadRequest as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
