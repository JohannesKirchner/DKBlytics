from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..utils import NotFound, Ambiguous, Conflict
from ..models import Category as CategoryORM
from ..schemas import (
    Category,
    CategoryCreate,
)


def _find_unique_category_by_name(db: Session, name: str) -> CategoryORM:
    """Return a single CategoryORM by name or raise Ambiguous/NotFound.

    Because category names are only unique *within a parent*,
    querying by name alone can be ambiguous. We detect that and surface
    a clear error so the API can respond 409 with guidance.
    """
    rows = db.scalars(select(CategoryORM).where(CategoryORM.name == name)).all()
    if not rows:
        raise NotFound(f"Category with name '{name}' was not found.")
    if len(rows) > 1:
        raise Ambiguous(
            f"Category name '{name}' is ambiguous (exists under multiple parents)."
        )
    return rows[0]


def _optional_unique_parent(
    parent_name: str, parents: Optional[List[CategoryORM]]
) -> Optional[CategoryORM]:
    if not parents:
        raise NotFound(f"Parent category with name '{parent_name}' does not exist.")
    if len(parents) > 1:
        raise Ambiguous(
            f"Parent category name '{parent_name}' is ambiguous (exists under multiple parents)."
        )
    return parents[0]


def create_category_db(db: Session, category: CategoryCreate) -> Category:
    if not category.parent_name:
        parent_obj = None
    else:
        parents = db.scalars(
            select(CategoryORM).where(CategoryORM.name == category.parent_name)
        ).all()
        parent_obj = _optional_unique_parent(category.parent_name, parents)

    obj = CategoryORM(
        name=category.name,
        parent_id=parent_obj.id if parent_obj else None,
    )

    try:
        db.add(obj)
        db.flush()  # get obj.id
    except IntegrityError as ie:
        db.rollback()
        # Likely violates uq_categories_parent_name
        raise Conflict(
            f"Category '{category.name}' already exists under the same parent."
        ) from ie

    return Category(
        id=obj.id,
        name=obj.name,
        parent_name=parent_obj.name if parent_obj else None,
    )


def get_all_categories_db(db: Session) -> List[Category]:
    rows: List[CategoryORM] = db.scalars(
        select(CategoryORM)
        .options(joinedload(CategoryORM.parent))
        .order_by(CategoryORM.name.asc())
    ).all()
    return [
        Category(
            id=r.id,
            name=r.name,
            parent_name=r.parent.name if r.parent else None,
        )
        for r in rows
    ]


def get_category_by_name_db(db: Session, name: str) -> Category:
    r = _find_unique_category_by_name(db, name)
    return Category(
        id=r.id,
        name=r.name,
        parent_name=r.parent.name if r.parent else None,
    )

def delete_category_db(db: Session, name: str) -> None:
    row = db.get(CategoryORM, name)
    if not row:
        raise NotFound(f"CategoryRule with name {name} was not found.")
    db.delete(row)
    # flush/commit handled by dependency


def build_category_tree_db(
    db: Session, parent_name: Optional[str] = None
) -> List[Dict]:
    """
    Return a nested category tree.

    - If parent_name is None: returns all root categories (no parent) with full subtrees.
    - If parent_name is provided: returns ONLY that category's direct children,
      each with its full subtree (the parent node itself is not included).
    """
    # Load all categories once
    rows: List[CategoryORM] = db.scalars(select(CategoryORM)).all()

    # Build nodes keyed by id
    by_id: Dict[int, Dict] = {
        r.id: {"id": r.id, "name": r.name, "children": []} for r in rows
    }

    # Link children -> parent
    for r in rows:
        if r.parent_id and r.parent_id in by_id:
            by_id[r.parent_id]["children"].append(by_id[r.id])

    # Determine roots according to parent_name
    if parent_name:
        # Because names are only unique within a parent, name-only lookups can be ambiguous.
        matches = [r for r in rows if r.name == parent_name]
        parent = _optional_unique_parent(parent_name, matches)
        roots = [by_id[r.id] for r in rows if r.parent_id == parent.id]
    else:
        # normal behavior: all roots (no parent)
        roots = [by_id[r.id] for r in rows if r.parent_id is None]

    return roots
