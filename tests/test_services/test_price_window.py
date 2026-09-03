from app.services.price_window import PriceWindow
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from app.schemas import Criteria

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def test_price_window():
    pw = PriceWindow(minimum=80, count=10, prices_sum=1000, standard_deviation=10)
    assert pw.mean() == 100.0
    assert pw.lower_bound() == 90.0
    assert pw.evaluate_price_criteria(70) == Criteria.LOWEST_PRICE
    assert pw.evaluate_price_criteria(90) == Criteria.LOWER_BOUND

def test_price_window_count_0():
    pw = PriceWindow(minimum=None, count=0, prices_sum=0, standard_deviation=None)
    assert pw.mean() is None
    assert pw.lower_bound() is None
    assert pw.evaluate_price_criteria(70) is None

def test_price_window_count_1():
    pw = PriceWindow(minimum=None, count=1, prices_sum=100, standard_deviation=10)
    assert pw.mean() == 100.0
    assert pw.lower_bound() is None
    assert pw.evaluate_price_criteria(70) is None
    assert pw.evaluate_price_criteria(90) is None


def test_price_window_count_minimum():
    pw = PriceWindow(minimum=None, count=6, prices_sum=600, standard_deviation=10)
    assert pw.mean() == 100.0
    assert pw.lower_bound() == 90.0
    assert pw.evaluate_price_criteria(70) is None
    assert pw.evaluate_price_criteria(90) is None

def test_price_window_from_history():
    db = mock_db_session()
    db.scalars.return_value.all.return_value = [100,100,100,100,100,100,100,100,100,100]
    pw = PriceWindow.from_history(db, 1)
    assert pw.count == 10
    assert pw.minimum == 100.0
    assert pw.prices_sum == 1000.0
    assert pw.standard_deviation == 0.0