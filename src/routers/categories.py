# routers/categories.py
from typing import List
from fastapi import APIRouter, HTTPException  # , Body
from ..models import Category  # , CategoryUpdate
from ..crud import (
    get_category_db,
    create_or_update_category,
    get_all_categories_db,
    # update_category_db,
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Category, status_code=201)
def create_category(category: Category):
    """
    Adds a new category. If the category rule already exists, it is updated.
    """
    create_or_update_category(category)
    return category


@router.get("/", response_model=List[Category])
def get_all_categories():
    """
    Retrieves all existing categories.
    """
    categories = get_all_categories_db()
    return [Category(**dict(row)) for row in categories]


@router.get("/{text}/{entity}", response_model=Category)
def get_category(text: str, entity: str):
    """
    Retrieves a specific category by text and entity.
    """
    category_data = get_category_db(text, entity)
    if category_data:
        return Category(**dict(category_data))
    raise HTTPException(status_code=404, detail="Category not found")


# @router.patch("/{text}/{entity}", response_model=Category)
# def update_category(text: str, entity: str, update_data: CategoryUpdate = Body(...)):
#     """
#     Updates the category name for an existing category rule.
#     """
#     if not update_category_db(text, entity, update_data.category):
#         raise HTTPException(status_code=404, detail="Category not found")

#     updated_category_data = get_category_db(text, entity)
#     return Category(**dict(updated_category_data))
