import pytest
from unittest.mock import patch
from app.core import PriceNotFound
from app.schemas import ProductToScrape, Criteria, DetectedProduct
from app.workers.scraper_task import ScraperTask

MODULE = "app.workers.scraper_task"

def make_products(n):
    return [ProductToScrape(id=i, title=f"Produto {i}", link=f"http://example.com/p{i}", viewers=[])
            for i in range(1, n + 1)]


@pytest.fixture
def mocks():
    with patch(f"{MODULE}.SessionLocal"), \
         patch(f"{MODULE}.sleep"), \
         patch(f"{MODULE}.PriceWindow") as price_window, \
         patch(f"{MODULE}.save_product_price_scheduler") as save_price, \
         patch(f"{MODULE}.save_error") as save_error, \
         patch(f"{MODULE}.has_open_error", return_value=False) as has_open_error, \
         patch(f"{MODULE}.create_detections") as create_detections:
        evaluate = price_window.from_history.return_value.evaluate_price_criteria
        evaluate.return_value = None
        yield {"evaluate": evaluate, "save_price": save_price,
               "save_error": save_error, "create_detections": create_detections, "has_open_error": has_open_error}


def run_with(products):
    task = ScraperTask()
    with patch.object(task, "_get_all_products", return_value=products):
        task.run()


def test_item_failure_does_not_stop_round(mocks):
    mocks["save_price"].side_effect = [PriceNotFound("sem preço"), 5000]
    run_with(make_products(2))
    assert mocks["save_price"].call_count == 2
    mocks["save_error"].assert_called_once()
    error = mocks["save_error"].call_args.args[1]
    assert error.product_id == 1
    assert error.error_type == "PriceNotFound"

def test_detection_created_when_criteria_fires(mocks):
    mocks["save_price"].return_value = 5000
    mocks["evaluate"].return_value = Criteria.LOWEST_PRICE
    run_with(make_products(1))
    mocks["create_detections"].assert_called_once()
    detected = mocks["create_detections"].call_args.args[1]
    assert isinstance(detected, DetectedProduct)
    assert detected.id == 1
    assert detected.price == 5000
    assert detected.criteria == Criteria.LOWEST_PRICE

def test_no_detection_without_criteria(mocks):
    mocks["save_price"].return_value = 5000
    run_with(make_products(1))
    mocks["create_detections"].assert_not_called()


def test_unexpected_error_saved_once_and_round_continues(mocks):
    mocks["save_price"].side_effect = [AttributeError("bug"), 5000]
    run_with(make_products(2))
    assert mocks["save_price"].call_count == 2
    mocks["save_error"].assert_called_once()
    assert mocks["save_error"].call_args.args[1].error_type == "AttributeError"

def test_unexpected_error_not_saved_when_already_open(mocks):
    mocks["save_price"].side_effect = [AttributeError("bug"), 5000]
    mocks["has_open_error"].return_value = True
    run_with(make_products(2))
    assert mocks["save_price"].call_count == 2
    mocks["save_error"].assert_not_called()