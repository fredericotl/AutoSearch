import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from app.core import ScraperBlocked
from app.scraper import AmazonScraper

URL = "https://www.amazon.com.br/dp/TESTE"


@pytest.fixture
def blocked_scraper():
    scraper = AmazonScraper()
    scraper.session = MagicMock()
    scraper.session.get.return_value.status_code = 403
    return scraper


def test_block_skips_requests_until_expired(blocked_scraper):
    with pytest.raises(ScraperBlocked):
        blocked_scraper.get_soup(URL)
    assert blocked_scraper.session.get.call_count == 1
    assert blocked_scraper.blocked_until is not None

    with pytest.raises(ScraperBlocked, match="Request skipped"):
        blocked_scraper.get_soup(URL)
    assert blocked_scraper.session.get.call_count == 1

    after_block = blocked_scraper.blocked_until + timedelta(minutes=1)
    with patch("app.scraper.base.now", return_value=after_block):
        with pytest.raises(ScraperBlocked):
            blocked_scraper.get_soup(URL)
    assert blocked_scraper.session.get.call_count == 2