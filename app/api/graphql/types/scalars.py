import decimal
from datetime import datetime, date
import strawberry

# Define scalar types
DateTime = strawberry.scalar(
    datetime,
    description="ISO-8601 formatted datetime",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: datetime.fromisoformat(v),
)

Date = strawberry.scalar(
    date,
    description="ISO-8601 formatted date",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: date.fromisoformat(v),
)

Numeric = strawberry.scalar(
    decimal.Decimal,
    description="Decimal number",
    serialize=lambda v: str(v),
    parse_value=lambda v: decimal.Decimal(v),
)