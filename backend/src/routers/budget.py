from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CategorySeriesPoint, SankeyResponse
from ..services.budget import build_sankey_db, category_series_db
from ..utils import BadRequest, NotFound

router = APIRouter(
    prefix="/budget",
    tags=["Budget"],
    responses={404: {"description": "Not found"}},
)


@router.get("/sankey", response_model=SankeyResponse)
def get_budget_sankey(
    db: Session = Depends(get_db),
    date_from: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    date_to: Optional[str] = Query(None, description="Inclusive YYYY-MM-DD."),
    account_id: Optional[str] = Query(None, description="Filter by account public_id."),
) -> SankeyResponse:
    """
    Full budget Sankey for the given period:
    Income -> Expenses + Savings, with the category subtrees on both sides.

    The frontend derives the expense-composition donut and the KPI numbers
    from this same payload. Savings is the synthetic delta income - expenses.
    """
    try:
        return build_sankey_db(
            db, date_from=date_from, date_to=date_to, account_id=account_id
        )
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/category-series", response_model=List[CategorySeriesPoint])
def get_category_series(
    db: Session = Depends(get_db),
    category_id: str = Query(
        ...,
        description="Category id whose subtree to sum, or 'uncategorized'.",
    ),
    account_id: Optional[str] = Query(None, description="Filter by account public_id."),
    granularity: str = Query("monthly", description="'monthly' or 'yearly'."),
    date_from: Optional[str] = Query(
        None, description="Inclusive YYYY-MM-DD; defaults to the earliest record."
    ),
    date_to: Optional[str] = Query(
        None, description="Inclusive YYYY-MM-DD; defaults to the latest record."
    ),
) -> List[CategorySeriesPoint]:
    """
    A category subtree's summed magnitude per bucket across the full history
    (gaps filled with 0). Drives the budget page's "over time" panel.
    """
    try:
        return category_series_db(
            db,
            category_id=category_id,
            account_id=account_id,
            granularity=granularity,
            date_from=date_from,
            date_to=date_to,
        )
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
