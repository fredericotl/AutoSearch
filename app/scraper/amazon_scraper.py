from app.scraper.base import Scraper
import re

class AmazonScraper(Scraper):
    def parse(self, soup) -> int|None:
        price = soup.find("span", class_="a-offscreen")
        if price is None:
            return None
        price_int = int(re.sub('[^0-9]', '', price.text))
        return price_int
