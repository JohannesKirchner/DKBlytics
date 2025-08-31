from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import CategoryRule, CategoryRuleCreate
from ..services.category_rules import (
    create_category_rule_db,
    get_category_rule_db,
    get_category_rule_by_id_db,
    get_all_category_rules_db,
    update_category_rule_by_text_and_entity_db,
    update_category_rule_by_entity_db,
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


@router.patch("/by-entity/{entity}")
def update_category_rules_by_entity(
    entity: str, category_id: int, db: Session = Depends(get_db)
):
    """
    Updates the category for all rules matching a given entity.
    """
    updated_count = update_category_rule_by_entity_db(db, entity, category_id)
    if updated_count == 0:
        raise HTTPException(
            status_code=404, detail=f"No category rules found for entity '{entity}'"
        )
    return {
        "message": f"Successfully updated {updated_count} categories for entity '{entity}'."
    }


@router.patch("/{text}/{entity}", response_model=CategoryRule)
def update_category_rule(
    text: str, entity: str, category_id: int, db: Session = Depends(get_db)
):
    """
    Updates the category name for a specific existing category rule.
    """
    if not update_category_rule_by_text_and_entity_db(db, text, entity, category_id):
        raise HTTPException(status_code=404, detail="Category rule not found")

    updated_category_data = get_category_rule_db(db, text, entity)
    if updated_category_data:
        return CategoryRule(**dict(updated_category_data))
    raise HTTPException(status_code=404, detail="Category not found after update.")
