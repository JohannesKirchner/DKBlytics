from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .categories import _find_unique_category_by_name
from ..utils import Conflict, NotFound
from ..models import CategoryRule as CategoryRuleORM
from ..schemas import (
    CategoryRule,
    CategoryRuleCreate,
)


def create_category_rule_db(db: Session, rule: CategoryRuleCreate) -> CategoryRule:
    # Find (unique) category by name
    cat = _find_unique_category_by_name(db, rule.category_name)

    # Enforce no text-only rules; entity must be present (schema already does this)
    # text can be None to mean "default for entity"
    obj = CategoryRuleORM(
        entity=rule.entity,
        text=rule.text,
        category_id=cat.id,
    )

    try:
        db.add(obj)
        db.flush()
    except IntegrityError as ie:
        db.rollback()
        # Could be uq_category_rules_entity_text or the partial unique on (entity WHERE text IS NULL)
        conflict_msg = (
            "A rule with this (entity, text) already exists."
            if rule.text is not None
            else "A default rule for this entity already exists."
        )
        raise Conflict(conflict_msg) from ie

    return CategoryRule(
        id=obj.id,
        entity=obj.entity,
        text=obj.text,
        category_name=cat.name,
    )


def get_all_category_rules_db(db: Session) -> List[CategoryRule]:
    rows: List[CategoryRuleORM] = db.scalars(
        select(CategoryRuleORM).options(joinedload(CategoryRuleORM.category))
    ).all()
    return [
        CategoryRule(
            id=r.id,
            entity=r.entity,
            text=r.text,
            category_name=r.category.name,
        )
        for r in rows
    ]


def delete_category_rule_db(db: Session, rule_id: int) -> None:
    row = db.get(CategoryRuleORM, rule_id)
    if not row:
        raise NotFound(f"CategoryRule with id {rule_id} was not found.")
    db.delete(row)
    # flush/commit handled by dependency


def _resolve_category_for_db_orm(
    db: Session, *, entity: str, text: Optional[str]
) -> Optional[CategoryRuleORM]:
    """Return the matching category ORM model for (entity, text) or None.

    Priority:
      1) exact: entity AND text match
      2) default: entity match AND text IS NULL
    """
    # 1) exact
    if text is not None:
        exact = db.scalars(
            select(CategoryRuleORM)
            .options(joinedload(CategoryRuleORM.category))
            .where(
                and_(
                    CategoryRuleORM.entity == entity,
                    CategoryRuleORM.text == text,
                )
            )
            .limit(1)
        ).first()
        if exact:
            return exact.category

    # 2) default for entity
    default = db.scalars(
        select(CategoryRuleORM)
        .options(joinedload(CategoryRuleORM.category))
        .where(
            and_(
                CategoryRuleORM.entity == entity,
                CategoryRuleORM.text.is_(None),
            )
        )
        .limit(1)
    ).first()
    return default.category if default else None


def resolve_category_for_db(
    db: Session, *, entity: str, text: Optional[str]
) -> Optional[str]:
    """Return the matching category name for (entity, text) or None.

    Priority:
      1) exact: entity AND text match
      2) default: entity match AND text IS NULL
    """
    category = _resolve_category_for_db_orm(db=db, entity=entity, text=text)
    return category.name if category else None
