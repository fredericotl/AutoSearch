from enum import Enum

class Criteria(str, Enum):
    LOWEST_PRICE = "lowest_price"
    LOWER_BOUND = "lower_bound"
    # THRESHOLD = "threshold" #TODO avaliar possível implementação
    # ANOMALY = "anomaly" #TODO construir lógica apos significância estatística pós MVP