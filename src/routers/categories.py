from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import Category, CategoryCreate
from ..services.utils import NotFound, Ambiguous, Conflict
from ..services.categories import (
    create_category_db,
    get_all_categories_db,
    get_category_by_name_db,
    build_category_tree_db,
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
    """Add a new category."""
    try:
        return create_category_db(db, category)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Ambiguous as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=List[Category])
def get_all_categories(db: Session = Depends(get_db)):
    """Retrieve all existing categories."""
    return get_all_categories_db(db)


@router.get("/tree", response_model=List[dict])
def get_category_tree(
    name: Optional[str] = Query(
        None,
        description="If provided, return only the children (with subtrees) of this category name.",
    ),
    db: Session = Depends(get_db),
):
    """Return a nested category tree.

    - No name -> all root categories (no parent) with full subtrees.
    - With name -> only that category's direct children (each with its subtree).
    """
    try:
        return build_category_tree_db(db, parent_name=name)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Ambiguous as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{name}", response_model=Category)
def get_category_by_name(name: str, db: Session = Depends(get_db)):
    """Retrieve a category by its name.

    Note: If multiple categories share this name under different parents,
    the request is considered ambiguous and returns 409.
    """
    try:
        return get_category_by_name_db(db, name)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Ambiguous as e:
        raise HTTPException(status_code=409, detail=str(e))
