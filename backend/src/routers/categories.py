from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import Category, CategoryCreate, CategoryUpdate
from ..utils import NotFound, Conflict
from ..services.categories import (
    create_category_db,
    get_all_categories_db,
    get_category_by_id_db,
    build_category_tree_db,
    delete_category_db,
    update_category_db,
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
):
    """Add a new category."""
    try:
        return create_category_db(db, category)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=List[Category])
def get_all_categories(db: Session = Depends(get_db)):
    """Retrieve all existing categories."""
    return get_all_categories_db(db)


@router.get("/tree", response_model=List[dict])
def get_category_tree(
    parent_id: Optional[int] = Query(
        None,
        description="If provided, return only the children (with subtrees) of this category id.",
    ),
    db: Session = Depends(get_db),
):
    """Return a nested category tree.

    - No parent_id -> all root categories with full subtrees.
    - With parent_id -> only that category's direct children (each with its subtree).
    """
    try:
        return build_category_tree_db(db, parent_id=parent_id)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{id}", response_model=Category)
def get_category(id: int, db: Session = Depends(get_db)):
    """Retrieve a category by its id."""
    try:
        return get_category_by_id_db(db, id)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{id}", response_model=Category)
def update_category(id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    """Rename a category by id."""
    try:
        return update_category_db(db, id, payload)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(id: int, db: Session = Depends(get_db)):
    """Delete a category by id."""
    try:
        delete_category_db(db, id)
        return
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
