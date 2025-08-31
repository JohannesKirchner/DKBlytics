from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import Category, CategoryCreate
from ..services.categories import (
    create_category_db,
    get_all_categories_db,
    get_category_by_name_db,
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=201, response_model=Category)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
):
    """
    Adds a new category.
    """
    category = create_category_db(db, category)
    return category


@router.get("/", response_model=List[Category])
def get_all_categories(db: Session = Depends(get_db)):
    """
    Retrieves all existing categories.
    """
    categories = get_all_categories_db(db)
    return [Category(**dict(row)) for row in categories]


@router.get("/{name}", response_model=Category)
def get_category_by_name(name: str, db: Session = Depends(get_db)):
    """
    Retrieves category by name
    """
    category = get_category_by_name_db(db, name)
    return category
