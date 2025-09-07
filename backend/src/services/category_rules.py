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

    # Validate rule type
    if rule.transaction_id is not None:
        # Transaction-specific rule - verify transaction exists
        from ..models import Transaction as TransactionORM
        
        transaction = db.get(TransactionORM, rule.transaction_id)
        if not transaction:
            raise NotFound(f"Transaction with id {rule.transaction_id} was not found.")
        
        if rule.entity is not None or rule.text is not None:
            raise Conflict("Transaction-specific rules should not have entity or text fields.")
        obj = CategoryRuleORM(
            transaction_id=rule.transaction_id,
            category_id=cat.id,
        )
    else:
        # General rule (entity/text based)
        if rule.entity is None:
            raise Conflict("Non-transaction rules must have an entity.")
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
        if rule.transaction_id is not None:
            conflict_msg = "A rule for this transaction already exists."
        else:
            conflict_msg = (
                "A rule with this (entity, text) already exists."
                if rule.text is not None
                else "A default rule for this entity already exists."
            )
        raise Conflict(conflict_msg) from ie

    return CategoryRule(
        id=obj.id,
        transaction_id=obj.transaction_id,
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
            transaction_id=r.transaction_id,
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
    db: Session, *, entity: str, text: Optional[str], transaction_id: Optional[int] = None
):
    """Return the matching category ORM model for (entity, text) or None.

    Priority:
      1) transaction-specific rule: transaction_id match
      2) exact: entity AND text match
      3) default: entity match AND text IS NULL
    """
    # 1) transaction-specific rule (highest priority)
    if transaction_id is not None:
        tx_rule = db.scalars(
            select(CategoryRuleORM)
            .options(joinedload(CategoryRuleORM.category))
            .where(CategoryRuleORM.transaction_id == transaction_id)
            .limit(1)
        ).first()
        if tx_rule:
            return tx_rule.category
    
    # 2) exact rule
    if text is not None:
        exact = db.scalars(
            select(CategoryRuleORM)
            .options(joinedload(CategoryRuleORM.category))
            .where(
                and_(
                    CategoryRuleORM.entity == entity,
                    CategoryRuleORM.text == text,
                    CategoryRuleORM.transaction_id.is_(None),  # Only general rules
                )
            )
            .limit(1)
        ).first()
        if exact:
            return exact.category

    # 3) default for entity
    default = db.scalars(
        select(CategoryRuleORM)
        .options(joinedload(CategoryRuleORM.category))
        .where(
            and_(
                CategoryRuleORM.entity == entity,
                CategoryRuleORM.text.is_(None),
                CategoryRuleORM.transaction_id.is_(None),  # Only general rules
            )
        )
        .limit(1)
    ).first()
    return default.category if default else None


def resolve_category_for_db(
    db: Session, *, entity: str, text: Optional[str], transaction_id: Optional[int] = None
) -> Optional[str]:
    """Return the matching category name for (entity, text) or None.

    Priority:
      1) transaction-specific rule: transaction_id match
      2) exact: entity AND text match
      3) default: entity match AND text IS NULL
    """
    category = _resolve_category_for_db_orm(db=db, entity=entity, text=text, transaction_id=transaction_id)
    return category.name if category else None


def recalculate_all_transaction_categories_db(db: Session) -> dict:
    """Recalculate categories for ALL transactions based on current rules.
    
    This is more comprehensive than apply_rules_to_uncategorized_transactions_db:
    - Updates ALL transactions, not just uncategorized ones
    - Handles rule deletion (removes categories when no rule matches)
    - Handles rule priority (exact rules override entity rules)
    - Handles rule updates
    
    Returns statistics about the recalculation.
    """
    from ..models import Transaction as TransactionORM
    
    # Get ALL transactions
    all_txs = db.scalars(select(TransactionORM)).all()
    
    stats = {
        'total_transactions': len(all_txs),
        'categorized': 0,
        'uncategorized': 0,
        'changed': 0
    }
    
    for tx in all_txs:
        # Store old category for change detection
        old_category_id = tx.category_id
        
        # Resolve the correct category using current rules
        category_orm = _resolve_category_for_db_orm(
            db, entity=tx.entity, text=tx.text, transaction_id=tx.id
        )
        
        # Update transaction category
        new_category_id = category_orm.id if category_orm else None
        tx.category_id = new_category_id
        
        # Update statistics
        if new_category_id:
            stats['categorized'] += 1
        else:
            stats['uncategorized'] += 1
            
        if old_category_id != new_category_id:
            stats['changed'] += 1
    
    # Commit all changes
    db.flush()
    
    return stats
