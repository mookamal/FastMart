"""add_analytics_fields

Revision ID: add_analytics_fields
Revises: dfa3bb5397d5
Create Date: 2025-05-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_analytics_fields'
down_revision: Union[str, None] = 'dfa3bb5397d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tags column to customers table
    op.add_column('customers', sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True))
    
    # Add discount_applications column to orders table
    op.add_column('orders', sa.Column('discount_applications', postgresql.JSONB(), nullable=True))
    
    # Add inventory_level column to products table
    op.add_column('products', sa.Column('inventory_levels', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('products', 'inventory_levels')
    op.drop_column('orders', 'discount_applications')
    op.drop_column('customers', 'tags')