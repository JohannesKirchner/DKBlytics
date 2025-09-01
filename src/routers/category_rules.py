from typing import List, Optional
from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import CategoryRule, CategoryRuleCreate
from ..services.category_rules import (
    create_category_rule_db,
    get_category_rule_by_id_db,
    get_all_category_rules_db,
)

router = APIRouter(
    prefix="/category-rules",
    tags=["CategoryRules"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=CategoryRule, status_code=status.HTTP_201_CREATED)
def create_category_rule(
    payload: CategoryRuleCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a Category Rule
    """
    category_rule = create_category_rule_db(db, payload)
    return category_rule


@router.get("/", response_model=List[CategoryRule])
def get_all_category_rules(
    text: Optional[str] = Query(None, description="Filter by transaction text"),
    entity: Optional[str] = Query(None, description="Filter by transaction entity"),
    db: Session = Depends(get_db),
):
    """
    Retrieves all existing categories.
    """
    categories = get_all_category_rules_db(db, text=text, entity=entity)
    return [CategoryRule(**dict(row)) for row in categories]


@router.get("/{category_id}/", response_model=CategoryRule)
def get_category_rule_by_id(
    category_id: int,
    db: Session = Depends(get_db),
):
    """
    Get category by ID
    """
    category_rule = get_category_rule_by_id_db(db, category_id)
    return category_rule
