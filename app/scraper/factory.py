from app.scraper import AmazonScraper
from app.core import UnsupportedScraper
from urllib.parse import urlparse
from app.scraper.base import Scraper

_scrapers: dict[str, Scraper] = {}

#TODO add outros scrapers
def get_scraper_for_link(link:str):
    domain = urlparse(link).netloc
    if "amazon" in domain or "a.co" in domain:
        if "amazon" not in _scrapers:
            _scrapers["amazon"] = AmazonScraper()
        return _scrapers["amazon"]
    # elif "mercadolivre" in link_lower:
    #     return MercadoLivreScraper()
    raise UnsupportedScraper(f"No support for {link}")