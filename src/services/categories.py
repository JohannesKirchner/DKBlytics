from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..models import Category as CategoryORM
from ..schemas import (
    Category,
    CategoryCreate,
)


def create_category_db(db: Session, category: CategoryCreate) -> Category:
    parent_obj = db.execute(
        select(CategoryORM).where(CategoryORM.name == category.parent_name)
    ).scalar_one_or_none()
    if category.parent_name and (parent_obj is None):
        db.rollback()
        raise ValueError(
            f"A parent category with name {category["parent"]} does not exist"
        )

    obj = CategoryORM(
        name=category.name, parent_id=parent_obj.id if parent_obj else None
    )
    db.add(obj)
    db.flush()
    return Category(
        id=obj.id, name=obj.name, parent_name=parent_obj.name if parent_obj else None
    )


def get_all_categories_db(db: Session) -> List[Category]:
    rows = db.scalars(select(CategoryORM).order_by(CategoryORM.name.asc())).all()
    return [
        Category(id=r.id, name=r.name, parent_name=r.parent.name if r.parent else None)
        for r in rows
    ]


def get_category_by_name_db(db: Session, name: str) -> Category:
    row = db.execute(
        select(CategoryORM)
        .options(joinedload(CategoryORM.parent))
        .where(CategoryORM.name == name)
    ).scalar_one_or_none()
    return Category(
        id=row.id, name=row.name, parent_name=row.parent.name if row.parent else None
    )


def build_category_tree(nodes: List[Category]) -> List[Dict]:
    # Build a nested tree in Python for the GET /categories/tree endpoint
    by_id = {n.id: {"id": n.id, "name": n.name, "children": []} for n in nodes}
    roots: List[Dict] = []
    for n in nodes:
        node = by_id[n.id]
        if n.parent_id and n.parent_id in by_id:
            by_id[n.parent_id]["children"].append(node)
        else:
            roots.append(node)

    # stable sort children by name
    def sort_subtree(sub):
        sub["children"].sort(key=lambda x: x["name"].lower())
        for ch in sub["children"]:
            sort_subtree(ch)

    for r in roots:
        sort_subtree(r)
    return roots
