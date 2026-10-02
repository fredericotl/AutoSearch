from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import timedelta, datetime, time
from app.models import PriceHistory
from app.schemas import Criteria
from app.core import now, WINDOW_OF_DAYS
from statistics import stdev
from sqlalchemy import select, func

class PriceWindow:

    MINIMUM_DATA_COUNT: int = 7

    def __init__(self, *, minimum: int | None, count: int, prices_sum: int | None, standard_deviation: float | None):
        self.count = count
        self.minimum = minimum
        self.prices_sum = prices_sum
        self.standard_deviation = standard_deviation


    @classmethod
    def from_history(cls, db:Session,  product_id: int):
        today = datetime.combine(now(), time.min)
        start = today - timedelta(days=WINDOW_OF_DAYS)
        captured_day = func.date(PriceHistory.captured_at)
        prices = db.scalars(select(func.min(PriceHistory.price))
        .where(PriceHistory.product_id == product_id,
                 PriceHistory.captured_at >= start,
                 PriceHistory.captured_at < today,
                 PriceHistory.price.is_not(None))
        .group_by(captured_day)).all()
        return cls.from_prices(list(prices))

    @classmethod
    def from_prices(cls, prices:list[int]):
        count = len(prices)
        if count == 0:
            minimum, prices_sum,standard_deviation  = None, None, None
        elif count == 1:
            minimum, prices_sum, standard_deviation = min(prices), sum(prices), None
        else:
            minimum, prices_sum, standard_deviation = min(prices), sum(prices), stdev(prices)
        return cls( minimum=minimum,count=count, prices_sum=prices_sum, standard_deviation=standard_deviation)

    # TODO Add outros critérios
    def evaluate_price_criteria(self, price_today: int) -> Criteria | None:
        if self.count < self.MINIMUM_DATA_COUNT:
            return None
        if self.minimum is not None and price_today < self.minimum:
            return Criteria.LOWEST_PRICE
        if self.standard_deviation is not None and price_today <= self.lower_bound():
            return Criteria.LOWER_BOUND
        return None

    def mean(self) -> float|None:
        if self.count == 0:
            return None
        return self.prices_sum/self.count

    def lower_bound(self) -> float|None:
        if self.count < 2:
            return None
        return self.mean()-self.standard_deviation


