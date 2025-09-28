"""baseline existing schema

Revision ID: 4112f706bcdb
Revises: 
Create Date: 2025-09-07 19:36:45.677348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4112f706bcdb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER COLUMN for nullability changes
    # So we need to recreate the table with the correct schema
    
    # 1. Create new table with correct schema
    op.create_table('category_rules_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('text', sa.String(length=1000), nullable=True),
        sa.Column('entity', sa.String(length=500), nullable=True),  # Now nullable
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('entity', 'text', name='uq_category_rules_entity_text'),
        sa.UniqueConstraint('transaction_id', name='uq_category_rules_transaction_id')
    )
    
    # 2. Copy existing data
    op.execute("""
        INSERT INTO category_rules_new (id, text, entity, category_id)
        SELECT id, text, entity, category_id FROM category_rules
    """)
    
    # 3. Drop old table
    op.drop_table('category_rules')
    
    # 4. Rename new table
    op.rename_table('category_rules_new', 'category_rules')
    
    # 5. Create indexes
    op.create_index(op.f('ix_category_rules_entity'), 'category_rules', ['entity'], unique=False)
    op.create_index(op.f('ix_category_rules_category_id'), 'category_rules', ['category_id'], unique=False)
    op.create_index(op.f('ix_category_rules_transaction_id'), 'category_rules', ['transaction_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate table without transaction_id and with entity NOT NULL
    
    # 1. Create old table structure
    op.create_table('category_rules_old',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('text', sa.String(length=1000), nullable=True),
        sa.Column('entity', sa.String(length=500), nullable=False),  # Back to NOT NULL
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('entity', 'text', name='uq_category_rules_entity_text')
    )
    
    # 2. Copy data (only rules with entity, skip transaction-specific rules)
    op.execute("""
        INSERT INTO category_rules_old (id, text, entity, category_id)
        SELECT id, text, entity, category_id FROM category_rules 
        WHERE entity IS NOT NULL
    """)
    
    # 3. Drop new table
    op.drop_table('category_rules')
    
    # 4. Rename old table back
    op.rename_table('category_rules_old', 'category_rules')
    
    # 5. Recreate original indexes
    op.create_index(op.f('ix_category_rules_entity'), 'category_rules', ['entity'], unique=False)
    op.create_index(op.f('ix_category_rules_category_id'), 'category_rules', ['category_id'], unique=False)
