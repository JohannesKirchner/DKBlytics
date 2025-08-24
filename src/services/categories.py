from typing import List, Optional, Dict
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..models import Category as CategoryORM, CategoryRule as CategoryRuleORM
from ..schemas import (
    Category,
    CategoryRule,
)


def create_category_db(
    db: Session, name: str, parent_id: Optional[int] = None
) -> Category:
    obj = CategoryORM(name=name, parent_id=parent_id)
    db.add(obj)
    db.refresh(obj)
    return Category(id=obj.id, name=obj.name, parent_id=obj.parent_id)


def get_all_categories_db(db: Session) -> List[Category]:
    rows = db.scalars(select(CategoryORM).order_by(CategoryORM.name.asc())).all()
    return [Category(id=r.id, name=r.name, parent_id=r.parent_id) for r in rows]


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


def get_all_category_rules_db(
    db: Session,
    *,
    text: Optional[str] = None,
    entity: Optional[str] = None,
    category_id: Optional[int] = None,
) -> List[CategoryRule]:
    stmt = select(CategoryRuleORM)
    if text:
        stmt = stmt.where(CategoryRuleORM.text == text)
    if entity:
        stmt = stmt.where(CategoryRuleORM.entity == entity)
    if category_id is not None:
        stmt = stmt.where(CategoryRuleORM.category_id == category_id)

    rows = db.scalars(
        stmt.order_by(CategoryRuleORM.entity.asc(), CategoryRuleORM.text.asc())
    ).all()
    return [
        CategoryRule(text=r.text, entity=r.entity, category_id=r.category_id)
        for r in rows
    ]


def get_category_rule_db(db: Session, text: str, entity: str) -> Optional[CategoryRule]:
    obj = db.get(CategoryRuleORM, {"text": text, "entity": entity})
    if not obj:
        return None
    return CategoryRule(text=obj.text, entity=obj.entity, category_id=obj.category_id)


def create_category_rule_if_not_exists(db: Session, text: str, entity: str) -> None:
    existing = db.get(CategoryRuleORM, {"text": text, "entity": entity})
    if not existing:
        db.add(CategoryRuleORM(text=text, entity=entity, category_id=None))


def update_category_rule_by_text_and_entity_db(
    db: Session, text: str, entity: str, category_id: Optional[int]
) -> bool:
    obj = db.get(CategoryRuleORM, {"text": text, "entity": entity})
    if not obj:
        return False
    obj.category_id = category_id
    return True


def update_category_rule_by_entity_db(
    db: Session, entity: str, category_id: Optional[int]
) -> int:
    result = db.execute(
        update(CategoryRuleORM)
        .where(CategoryRuleORM.entity == entity)
        .values(category_id=category_id)
    )
    return result.rowcount or 0
