from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body, Query
from ..models import Category, CategoryUpdate
from ..crud import (
    get_category_db,
    create_or_update_category,
    get_all_categories_db,
    update_category_by_text_and_entity_db,
    update_category_by_entity_db,
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Category, status_code=201)
def create_category(category: Category):
    """
    Adds or updates a category rule.
    """
    create_or_update_category(category)
    return category


@router.get("/", response_model=List[Category])
def get_all_categories(
    text: Optional[str] = Query(None, description="Filter by transaction text"),
    entity: Optional[str] = Query(None, description="Filter by transaction entity"),
):
    """
    Retrieves all existing categories.
    """
    categories = get_all_categories_db(text=text, entity=entity)
    return [Category(**dict(row)) for row in categories]


@router.patch("/by-entity/{entity}")
def update_categories_by_entity(entity: str, update_data: CategoryUpdate):
    """
    Updates the category for all rules matching a given entity.
    """
    updated_count = update_category_by_entity_db(entity, update_data.category)
    if updated_count == 0:
        raise HTTPException(
            status_code=404, detail=f"No category rules found for entity '{entity}'"
        )
    return {
        "message": f"Successfully updated {updated_count} categories for entity '{entity}'."
    }


@router.patch("/{text}/{entity}", response_model=Category)
def update_category(text: str, entity: str, update_data: CategoryUpdate):
    """
    Updates the category name for a specific existing category rule.
    """
    if not update_category_by_text_and_entity_db(text, entity, update_data.category):
        raise HTTPException(status_code=404, detail="Category rule not found")

    updated_category_data = get_category_db(text, entity)
    if updated_category_data:
        return Category(**dict(updated_category_data))
    raise HTTPException(status_code=404, detail="Category not found after update.")
