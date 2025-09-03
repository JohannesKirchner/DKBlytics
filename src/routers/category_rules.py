from typing import List, Optional
from fastapi import APIRouter, Query, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import CategoryRule, CategoryRuleCreate
from ..services.utils import NotFound, Ambiguous, Conflict
from ..services.category_rules import (
    create_category_rule_db,
    get_all_category_rules_db,
    delete_category_rule_db,
    resolve_category_for_db,
)

router = APIRouter(
    prefix="/rules",
    tags=["Category Rules"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=CategoryRule, status_code=status.HTTP_201_CREATED)
def create_category_rule(
    payload: CategoryRuleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a category rule.

    Matching priority:
      1) exact match on (entity AND text)
      2) default match on (entity AND text IS NULL)
    """
    try:
        return create_category_rule_db(db, payload)
    except NotFound as e:
        # category_name not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Ambiguous as e:
        # category_name ambiguous across parents
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Conflict as e:
        # duplicate (entity, text) or duplicate default for entity
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=List[CategoryRule])
def get_all_category_rules(db: Session = Depends(get_db)):
    """List all category rules."""
    return get_all_category_rules_db(db)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a category rule by id."""
    try:
        delete_category_rule_db(db, rule_id)
        return
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/resolve", response_model=Optional[str])
def resolve_rule(
    entity: str = Query(..., description="Transaction entity"),
    text: Optional[str] = Query(None, description="Transaction text/description"),
    db: Session = Depends(get_db),
):
    """
    Resolve a category name for a given (entity, text).

    Resolution order:
      1) exact (entity AND text)
      2) default (entity AND text IS NULL)
    Returns the category name or null if no match.
    """
    return resolve_category_for_db(db, entity=entity, text=text)
