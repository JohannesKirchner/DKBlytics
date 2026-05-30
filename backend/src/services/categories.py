from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..utils import NotFound, Ambiguous, Conflict
from ..models import Category as CategoryORM
from ..schemas import (
    Category,
    CategoryCreate,
    CategoryUpdate,
)

ROOT_CATEGORY_NAMES = ("Einnahmen", "Ausgaben")


def _find_unique_category_by_name(db: Session, name: str) -> CategoryORM:
    """Internal helper for modules that resolve categories by name (e.g.
    transaction-filtering by scope, or rule creation). Names are unique only
    within a parent, so this raises Ambiguous on collisions."""
    rows = db.scalars(select(CategoryORM).where(CategoryORM.name == name)).all()
    if not rows:
        raise NotFound(f"Category with name '{name}' was not found.")
    if len(rows) > 1:
        raise Ambiguous(
            f"Category name '{name}' is ambiguous (exists under multiple parents)."
        )
    return rows[0]


def _to_schema(row: CategoryORM) -> Category:
    return Category(
        id=row.id,
        name=row.name,
        parent_name=row.parent.name if row.parent else None,
    )


def _get_or_404(db: Session, id: int) -> CategoryORM:
    row = db.get(CategoryORM, id)
    if row is None:
        raise NotFound(f"Category with id {id} was not found.")
    return row


def _is_protected_root(row: CategoryORM) -> bool:
    return row.parent_id is None and row.name in ROOT_CATEGORY_NAMES


def create_category_db(db: Session, category: CategoryCreate) -> Category:
    parent_obj: Optional[CategoryORM] = None
    if category.parent_id is not None:
        parent_obj = db.get(CategoryORM, category.parent_id)
        if parent_obj is None:
            raise NotFound(
                f"Parent category with id {category.parent_id} does not exist."
            )

    obj = CategoryORM(
        name=category.name,
        parent_id=parent_obj.id if parent_obj else None,
    )
    try:
        db.add(obj)
        db.flush()
    except IntegrityError as ie:
        db.rollback()
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
    return [_to_schema(r) for r in rows]


def get_category_by_id_db(db: Session, id: int) -> Category:
    return _to_schema(_get_or_404(db, id))


def update_category_db(db: Session, id: int, update: CategoryUpdate) -> Category:
    row = _get_or_404(db, id)
    if _is_protected_root(row):
        raise Conflict(f"Root category '{row.name}' cannot be renamed.")

    row.name = update.name
    try:
        db.flush()
    except IntegrityError as ie:
        db.rollback()
        raise Conflict(
            f"Category '{update.name}' already exists under the same parent."
        ) from ie

    return _to_schema(row)


def delete_category_db(db: Session, id: int) -> None:
    row = _get_or_404(db, id)
    if _is_protected_root(row):
        raise Conflict(f"Root category '{row.name}' cannot be deleted.")
    # ORM cascade on the `children` and `rules` backrefs removes descendants
    # and any rules that pointed at deleted categories. Transactions get
    # category_id NULLed via the FK's ON DELETE SET NULL.
    db.delete(row)


def build_category_tree_db(
    db: Session, parent_id: Optional[int] = None
) -> List[Dict]:
    """
    Return a nested category tree.

    - If parent_id is None: returns all root categories with full subtrees.
    - If parent_id is provided: returns ONLY that category's direct children,
      each with its full subtree (the parent node itself is not included).
    """
    if parent_id is not None and db.get(CategoryORM, parent_id) is None:
        raise NotFound(f"Parent category with id {parent_id} does not exist.")

    rows: List[CategoryORM] = db.scalars(select(CategoryORM)).all()

    by_id: Dict[int, Dict] = {
        r.id: {"id": r.id, "name": r.name, "children": []} for r in rows
    }
    for r in rows:
        if r.parent_id and r.parent_id in by_id:
            by_id[r.parent_id]["children"].append(by_id[r.id])

    if parent_id is not None:
        roots = [by_id[r.id] for r in rows if r.parent_id == parent_id]
    else:
        roots = [by_id[r.id] for r in rows if r.parent_id is None]
    return roots


def ensure_root_categories_db(db: Session) -> None:
    """Idempotently seed the two top-level roots (Einnahmen, Ausgaben).

    Safe to call repeatedly: only creates rows that are missing.
    """
    existing = {
        r.name
        for r in db.scalars(
            select(CategoryORM).where(CategoryORM.parent_id.is_(None))
        ).all()
    }
    for name in ROOT_CATEGORY_NAMES:
        if name not in existing:
            db.add(CategoryORM(name=name, parent_id=None))
    db.flush()
