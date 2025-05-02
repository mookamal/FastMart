from app.api.graphql.types.scalars import Date
import strawberry
from typing import Optional

@strawberry.input
class DateRangeInput:
    start_date: Date
    end_date: Date

@strawberry.input
class PaginationInput:
    limit: int = 20
    offset: int = 0

@strawberry.input
class SortingInput:
    sort_by: Optional[str] = None
    sort_desc: bool = False