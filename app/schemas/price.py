from enum import Enum

class Criteria(str, Enum):
    LOWEST_PRICE = "lowest_price"
    LOWER_BOUND = "lower_bound"