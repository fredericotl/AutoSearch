from app.scraper.base import Scraper
import re

class AmazonScraper(Scraper):
    def parse(self, soup) -> int|None:
        price = soup.select_one("#corePrice_feature_div .apex-pricetopay-value .a-offscreen")
        if price is None:
            return None
        digits = re.sub('[^0-9]', '', price.text)
        if not digits:
            return None
        return int(digits)
