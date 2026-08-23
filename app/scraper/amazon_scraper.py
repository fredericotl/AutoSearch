from app.scraper.base import Scraper
import re
class AmazonScraper(Scraper):
    def parse(self, soup) -> int|None:
        price = soup.find("span", class_="a-offscreen")
        if price is None:
            return None
        price_int = int(re.sub('[^0-9]', '', price.text))
        return price_int

if __name__ == "__main__":
    scp = AmazonScraper()
    price = scp.get_price("https://www.amazon.com.br/Geladeira-Duplex-Consul-Freezer-Embaixo/dp/B0G6724M4Z/ref=sr_1_2_sspa?crid=2VOQYS1KKPWZO&dib=eyJ2IjoiMSJ9.hxCIdqRUwaHUVgnAAK4_55V2VKVcSyc8NWA-5yqdUIa6yP6sJtbnyN7RRY3-Ldch-gC5A1-0BUULbmNwoack5Z8tLmVKHGRWZ0wDL2KUZQsWRUUZgoaG9OnPkD1udYyPi5Jw4jrYOd1bsV535PJ43mKFLWkzSnCNPz5zGFEiPyi24lg7rOdHNbMysGYepPnc45BpfgbLIaAHYuFhJ10NmuAdls8Zg6gga_1mhCvMrSXUCjnmOL4sILXpZA3JIsPhyttPQTBC91MNtI4ZM9Nx3OQU6cBx2ec7595VS3KcSDA.uqjIRMW8v3DSPknh99TC43OYmyJH0hZ8pgdvzJbh0xU&dib_tag=se&keywords=geladeira&qid=1785956842&sprefix=geladeira%2Caps%2C224&sr=8-2-spons&ufe=app_do%3Aamzn1.fos.95de73c3-5dda-43a7-bd1f-63af03b14751&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1")
    print(price)