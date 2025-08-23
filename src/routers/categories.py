from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..models import Category, CategoryRule
from ..crud import (
    get_category_rule_db,
    create_category_db,
    get_all_categories_db,
    get_all_category_rules_db,
    update_category_rule_by_text_and_entity_db,
    update_category_rule_by_entity_db,
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=201)
def create_category(name, parent_id):
    """
    Adds a new category.
    """
    category_id = create_category_db(name, parent_id)
    return category_id


@router.get("/", response_model=List[Category])
def get_all_categories():
    """
    Retrieves all existing categories.
    """
    categories = get_all_categories_db()
    return [Category(**dict(row)) for row in categories]


@router.get("rules/", response_model=List[CategoryRule])
def get_all_category_rules(
    text: Optional[str] = Query(None, description="Filter by transaction text"),
    entity: Optional[str] = Query(None, description="Filter by transaction entity"),
):
    """
    Retrieves all existing categories.
    """
    categories = get_all_category_rules_db(text=text, entity=entity)
    return [CategoryRule(**dict(row)) for row in categories]


@router.patch("rules/by-entity/{entity}")
def update_category_rules_by_entity(entity: str, category_id: int):
    """
    Updates the category for all rules matching a given entity.
    """
    updated_count = update_category_rule_by_entity_db(entity, category_id)
    if updated_count == 0:
        raise HTTPException(
            status_code=404, detail=f"No category rules found for entity '{entity}'"
        )
    return {
        "message": f"Successfully updated {updated_count} categories for entity '{entity}'."
    }


@router.patch("rules/{text}/{entity}", response_model=CategoryRule)
def update_category_rule(text: str, entity: str, category_id: int):
    """
    Updates the category name for a specific existing category rule.
    """
    if not update_category_rule_by_text_and_entity_db(text, entity, category_id):
        raise HTTPException(status_code=404, detail="Category rule not found")

    updated_category_data = get_category_rule_db(text, entity)
    if updated_category_data:
        return CategoryRule(**dict(updated_category_data))
    raise HTTPException(status_code=404, detail="Category not found after update.")
