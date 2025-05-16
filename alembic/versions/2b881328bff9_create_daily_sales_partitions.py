"""create_daily_sales_partitions

Revision ID: 2b881328bff9
Revises: c3326ed63111
Create Date: 2025-05-17 00:15:51.324519
"""
from alembic import op
import sqlalchemy as sa
from datetime import date

# revision identifiers, used by Alembic.
revision = '2b881328bff9'
down_revision = 'c3326ed63111'
branch_labels = None
depends_on = None


def upgrade() -> None:
    start = date(2019, 1, 1)
    end = date(2031, 1, 1)
    current = start
    while current < end:
        year = current.year
        month = current.month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        next_date = date(next_year, next_month, 1)
        partition_name = f"daily_sales_analytics_y{year}m{month:02d}"

        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF daily_sales_analytics
            FOR VALUES FROM ('{current}') TO ('{next_date}');
        """)
        current = next_date


def downgrade() -> None:
    pass
