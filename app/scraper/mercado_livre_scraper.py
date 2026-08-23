from app.scraper.base import Scraper
import re
class MercadoLivreScraper(Scraper):
    def parse(self, soup) -> int|None:
        price_whole = soup.find("span", class_="andes-money-amount__fraction")
        if price_whole is None:
            return None
        price_whole_int = int(re.sub('[^0-9]', '', price_whole.text))
        price_fraction = soup.find("span", class_="andes-money-amount__cents andes-money-amount__cents")
        if price_fraction is None:
            price_fraction_int = 0
        else:
            price_fraction_int = int(re.sub('[^0-9]', '', price_fraction.text))
        price_int = price_whole_int*100 + price_fraction_int
        return price_int
    def _warm_up(self, session):
        session.get("https://www.mercadolivre.com.br/", headers=self.HEADER, timeout=self.TIMEOUT)

if __name__ == "__main__":
    scp = MercadoLivreScraper()
    price = scp.get_price("https://www.mercadolivre.com.br/geladeira-electrolux-frost-free-inverter-490l-com-autosense-inverse-black-inox-look-ib7b/p/MLB37034006?product_trigger_id=MLB37034004&attributes=COLOR%3APreto%2CVOLTAGE%3AMLB37034006&picker=true&quantity=1")
    print(price)