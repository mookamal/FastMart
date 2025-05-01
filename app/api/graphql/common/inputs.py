from app.api.graphql.types.scalars import Date
import strawberry

@strawberry.input
class DateRangeInput:
    start_date: Date
    end_date: Date