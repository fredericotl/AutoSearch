from app.services.price_service import (save_product_price_api, save_product_price_scheduler, price_str,
                                        build_price_info, PriceInfo, ProductPrices, get_prices_by_products)
from app.schemas import ProductPriceResponse, ProductToScrape
from app.core import PriceNotFound
from app.core import now
from unittest.mock import MagicMock, patch
from app.models import Product, PriceHistory
import pytest
from datetime import timedelta

def mock_db_session():
    mock_session = MagicMock()
    return mock_session

def mock_product(pd_id:int =1):
    mock_product = MagicMock(spec=Product)
    mock_product.id = pd_id
    mock_product.title = "Test Product"
    mock_product.link = "https://amazon.com/dp/B001"
    return mock_product


def test_save_product_price_api_from_db():
    db = mock_db_session()
    product_model = mock_product()
    product_to_scrape = ProductToScrape(id=product_model.id, title=product_model.title, link=product_model.link,
                                        viewers=[])

    db.query.return_value.filter.return_value.first.return_value = PriceHistory(product_id=product_model.id, price=100.0)

    result = save_product_price_api(db, product_to_scrape)

    assert isinstance(result, ProductPriceResponse)
    assert result.title == "Test Product"
    assert result.link == "https://amazon.com/dp/B001"
    assert result.status == "from_db"
    assert result.price == 100.0

def test_save_product_price_api_scraped():
    db = mock_db_session()
    product_model = mock_product()
    product_to_scrape = ProductToScrape(id=product_model.id, title=product_model.title, link=product_model.link,
                                        viewers=[])

    db.query.return_value.filter.return_value.first.return_value = None

    with patch('app.services.price_service.get_scraper_for_link') as mock_get_scraper:
        mock_scraper = MagicMock()
        mock_scraper.get_price.return_value = 100.0
        mock_get_scraper.return_value = mock_scraper

        result = save_product_price_api(db, product_to_scrape)

        assert isinstance(result, ProductPriceResponse)
        assert result.title == "Test Product"
        assert result.link == "https://amazon.com/dp/B001"
        assert result.status == "scraped"
        assert result.price == 100.0

def test_save_product_price_scheduler_success():
    db = mock_db_session()
    product_to_scrape = ProductToScrape(id=1, title="Test Product",
                                        link="https://amazon.com/dp/B001", viewers=[])

    db.query.return_value.filter.return_value.first.return_value = None

    with patch('app.services.price_service.get_scraper_for_link') as mock_get_scraper:
        mock_scraper = MagicMock()
        mock_scraper.get_price.return_value = 14999
        mock_get_scraper.return_value = mock_scraper

        result = save_product_price_scheduler(db, product_to_scrape)
        assert result == 14999

def test_save_product_price_scheduler_no_price():
    db = mock_db_session()
    product_model = mock_product()
    product_to_scrape = ProductToScrape(id=product_model.id, title=product_model.title, link=product_model.link,
                                        viewers=[])

    db.query.return_value.filter.return_value.first.return_value = None

    with patch('app.services.price_service.get_scraper_for_link') as mock_get_scraper:
        mock_scraper = MagicMock()
        mock_scraper.get_price.return_value = None
        mock_get_scraper.return_value = mock_scraper

        with pytest.raises(PriceNotFound):
            save_product_price_scheduler(db, product_to_scrape)

def test_price_str():
    price1 = price_str(15677)
    price2 = price_str(1567700)
    price3 = price_str(15607)
    price4 = price_str(7)
    assert price1 == "R$ 156,77"
    assert price2 == "R$ 15.677,00"
    assert price3 == "R$ 156,07"
    assert price4 == "R$ 0,07"

def test_get_prices_by_products():
    db = mock_db_session()
    db.execute.return_value.fetchall.return_value = []
    prices = get_prices_by_products(db, {1})
    assert prices == {1: ProductPrices(history=[], price_today=None)}
    db.execute.return_value.fetchall.return_value = [
        (1, 150, now() - timedelta(days=2)),
        (1, 100, now()),]
    prices = get_prices_by_products(db, {1})
    assert prices == {1: ProductPrices(history=[150, 100], price_today=100)}
    prices = get_prices_by_products(db, {1,2})
    assert prices == {1: ProductPrices(history=[150, 100], price_today=100), 2: ProductPrices(history=[], price_today=None)}
    db.execute.return_value.fetchall.return_value = [
        (1, 150, now() - timedelta(days=2)),
        (1, 100, now()),
        (2, 200, now()),]
    prices = get_prices_by_products(db, {1,2})
    assert prices == {1: ProductPrices(history=[150, 100], price_today=100), 2: ProductPrices(history=[200], price_today=200)}
    db.execute.return_value.fetchall.return_value = [
        (1, 150, now() - timedelta(days=2)),
        (1, 100, now()),
        (2, 200, now()- timedelta(days=2)),]
    prices = get_prices_by_products(db, {1, 2})
    assert prices == {1: ProductPrices(history=[150, 100], price_today=100), 2: ProductPrices(history=[200], price_today=None)}


def test_build_price_info():
    price_info = build_price_info([100, 200, 300])
    assert isinstance(price_info, PriceInfo)
    assert price_info.mean == 'R$ 2,00'
    assert price_info.lowest_price == 'R$ 1,00'

def test_build_price_info_empty():
    price_info = build_price_info([])
    assert isinstance(price_info, PriceInfo)
    assert price_info.mean is None
    assert price_info.lowest_price is None

def test_build_price_info_round_mean():
    price_info = build_price_info([7, 11, 13])
    assert isinstance(price_info, PriceInfo)
    assert price_info.mean == 'R$ 0,10'