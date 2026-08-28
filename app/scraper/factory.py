from app.scraper import AmazonScraper
from app.core.exceptions import UnsupportedScraper
from urllib.parse import urlparse


#TODO add outros scrapers
def get_scraper_for_link(link:str):
    domain = urlparse(link).netloc
    if "amazon" in domain or "a.co" in domain:
        return AmazonScraper()
    # elif "mercadolivre" in link_lower:
    #     return MercadoLivreScraper()
    raise UnsupportedScraper(f"No support for {link}")