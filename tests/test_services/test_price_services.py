from app.services.price_service import save_product_price_api, save_product_price_scheduler
from app.schemas import ProductPriceResponse, ProductToScrape
from app.core import PriceNotFound
from unittest.mock import MagicMock, patch
from app.models import Product, PriceHistory
import pytest

def mock_db_session():
    mock_session = MagicMock()
    return mock_session

def mock_product():
    mock_product = MagicMock(spec=Product)
    mock_product.id = 1
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