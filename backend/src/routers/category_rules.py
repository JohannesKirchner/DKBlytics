from typing import List, Optional

from fastapi import APIRouter, Query, Depends, status, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CategoryRule, CategoryRuleCreate
from ..utils import NotFound, Ambiguous, Conflict
from ..services.category_rules import (
    create_category_rule_db,
    get_all_category_rules_db,
    delete_category_rule_db,
    resolve_category_for_db,
    recalculate_transaction_categories_db,
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
    Create a category rule (general or transaction-specific).

    Rule hierarchy:
      1) transaction-specific rule (transaction_id match)
      2) exact match on (entity AND text)  
      3) default match on (entity AND text IS NULL)
      
    After creating the rule, automatically recalculates matching transactions only.
    """
    try:
        rule = create_category_rule_db(db, payload)
        recalculate_transaction_categories_db(
            db,
            transaction_id=rule.transaction_id,
            entity=rule.entity,
            text=rule.text,
        )
        
        return rule
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
    """Delete a category rule by id.
    
    After deleting the rule, recalculates only the transactions that could be
    affected by the removed scope.
    """
    try:
        deleted_scope = delete_category_rule_db(db, rule_id)
        recalculate_transaction_categories_db(db, **deleted_scope)
        
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
    
    Note: This endpoint only resolves general rules (entity/text based).
    For transaction-specific rules, use the transaction endpoints directly.

    Resolution order:
      1) exact (entity AND text)
      2) default (entity AND text IS NULL)
    Returns the category name or null if no match.
    """
    return resolve_category_for_db(db, entity=entity, text=text)


@router.post("/apply", status_code=status.HTTP_200_OK)
def apply_rules_to_transactions(
    transaction_id: Optional[int] = Query(
        None,
        description="Limit recalculation to a specific transaction.",
    ),
    entity: Optional[str] = Query(
        None,
        description="Limit recalculation to transactions matching this entity.",
    ),
    text: Optional[str] = Query(
        None,
        description="When entity is provided, further filter by description/text.",
    ),
    db: Session = Depends(get_db),
):
    """
    Recalculate categories for a subset of transactions based on current rules.
    When no filters are provided this still updates all transactions.
    """
    try:
        stats = recalculate_transaction_categories_db(
            db,
            transaction_id=transaction_id,
            entity=entity,
            text=text,
        )
        return {
            "message": f"Recalculated {stats['total_transactions']} transactions",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
