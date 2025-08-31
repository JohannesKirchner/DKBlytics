from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..models import CategoryRule as CategoryRuleORM, Category as CategoryORM
from ..schemas import (
    CategoryRule,
    CategoryRuleCreate,
)


def create_category_rule_db(
    db: Session, category_rule: CategoryRuleCreate
) -> CategoryRule:
    category_id = db.execute(
        select(CategoryORM.id).where(CategoryORM.name == category_rule.category_name)
    ).scalar_one_or_none()
    if category_id is None:
        db.rollback()
        raise ValueError(
            f"A category with name {category_rule.category_name} does not exist"
        )

    obj = CategoryRuleORM(
        text=category_rule.text,
        entity=category_rule.entity,
        category_id=category_id,
    )
    db.add(obj)
    db.flush()
    return CategoryRule(
        id=obj.id,
        text=obj.text,
        entity=obj.entity,
        category_name=category_rule.category_name,
    )


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
        CategoryRule(
            id=r.id,
            text=r.text,
            entity=r.entity,
            category_name=r.category.name,
        )
        for r in rows
    ]


def get_category_rule_db(db: Session, text: str, entity: str) -> Optional[CategoryRule]:
    obj = db.execute(
        select(CategoryRuleORM).where(
            CategoryRuleORM.text == text, CategoryRuleORM.entity == entity
        )
    )
    if not obj:
        return None
    return CategoryRule(text=obj.text, entity=obj.entity, category_id=obj.category_id)


def get_category_rule_by_id_db(db: Session, category_id: int) -> CategoryRule:
    obj = db.execute(
        select(CategoryRuleORM).where(CategoryRuleORM.id == category_id)
    ).scalar_one_or_none()
    return CategoryRule(
        id=obj.id, text=obj.text, entity=obj.entity, category_name=obj.category.name
    )


def update_category_rule_by_text_and_entity_db(
    db: Session, text: str, entity: str, category_id: Optional[int]
) -> bool:
    obj = db.execute(
        select(CategoryRuleORM).where(
            CategoryRuleORM.text == text, CategoryRuleORM.entity == entity
        )
    )
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
