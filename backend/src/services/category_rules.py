from typing import Dict, List, NamedTuple, Optional, Tuple

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


class _RuleMatch(NamedTuple):
    category_id: int
    category_name: str


class RulesIndex:
    """Loads all category rules in one query and resolves categories in memory."""

    def __init__(self, db: Session) -> None:
        rules = db.scalars(
            select(CategoryRuleORM).options(joinedload(CategoryRuleORM.category))
        ).all()
        self._tx: Dict[int, _RuleMatch] = {}
        self._entity_text: Dict[Tuple[str, str], _RuleMatch] = {}
        self._entity_default: Dict[str, _RuleMatch] = {}

        for r in rules:
            match = _RuleMatch(r.category.id, r.category.name)
            if r.transaction_id is not None:
                self._tx[r.transaction_id] = match
            elif r.entity is not None and r.text is not None:
                self._entity_text[(r.entity, r.text)] = match
            elif r.entity is not None:
                self._entity_default[r.entity] = match

    def resolve(
        self,
        entity: str,
        text: Optional[str],
        transaction_id: Optional[int] = None,
    ) -> Optional[_RuleMatch]:
        if transaction_id is not None:
            match = self._tx.get(transaction_id)
            if match:
                return match
        if text is not None:
            match = self._entity_text.get((entity, text))
            if match:
                return match
        return self._entity_default.get(entity)

    def resolve_name(
        self,
        entity: str,
        text: Optional[str],
        transaction_id: Optional[int] = None,
    ) -> Optional[str]:
        match = self.resolve(entity, text, transaction_id)
        return match.category_name if match else None


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

    # Recalculate affected transactions so category_id stays current
    if rule.transaction_id is not None:
        recalculate_transaction_categories_db(db, transaction_id=rule.transaction_id)
    elif rule.text is not None:
        recalculate_transaction_categories_db(db, entity=rule.entity, text=rule.text)
    else:
        recalculate_transaction_categories_db(db, entity=rule.entity)

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


def delete_category_rule_db(db: Session, rule_id: int) -> dict:
    row = db.get(CategoryRuleORM, rule_id)
    if not row:
        raise NotFound(f"CategoryRule with id {rule_id} was not found.")

    rule_scope = {
        "transaction_id": row.transaction_id,
        "entity": row.entity,
        "text": row.text,
    }

    db.delete(row)
    db.flush()

    # Recalculate affected transactions so category_id reflects the removed rule
    if rule_scope["transaction_id"] is not None:
        recalculate_transaction_categories_db(db, transaction_id=rule_scope["transaction_id"])
    elif rule_scope["entity"] is not None and rule_scope["text"] is not None:
        recalculate_transaction_categories_db(db, entity=rule_scope["entity"], text=rule_scope["text"])
    elif rule_scope["entity"] is not None:
        recalculate_transaction_categories_db(db, entity=rule_scope["entity"])

    return rule_scope


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


def recalculate_transaction_categories_db(
    db: Session,
    *,
    transaction_id: Optional[int] = None,
    entity: Optional[str] = None,
    text: Optional[str] = None,
) -> dict:
    """Recalculate transaction categories for a filtered subset.

    Without filters all transactions are recalculated. Providing
    ``transaction_id`` takes precedence over entity/text filters.
    Uses a single bulk rules load to avoid N+1 queries.
    """

    from ..models import Transaction as TransactionORM

    query = select(TransactionORM)

    if transaction_id is not None:
        query = query.where(TransactionORM.id == transaction_id)
    else:
        if entity is not None:
            query = query.where(TransactionORM.entity == entity)
        if text is not None:
            query = query.where(TransactionORM.text == text)

    txs = db.scalars(query).all()

    rules_index = RulesIndex(db)

    stats = {
        'total_transactions': len(txs),
        'categorized': 0,
        'uncategorized': 0,
        'changed': 0,
    }

    for tx in txs:
        old_category_id = tx.category_id
        match = rules_index.resolve(tx.entity, tx.text, tx.id)
        new_category_id = match.category_id if match else None
        tx.category_id = new_category_id

        if new_category_id:
            stats['categorized'] += 1
        else:
            stats['uncategorized'] += 1

        if old_category_id != new_category_id:
            stats['changed'] += 1

    db.flush()

    return stats
