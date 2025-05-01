from enum import Enum
import strawberry

# Common enums that can be shared across features

@strawberry.enum
class TimeInterval(Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"