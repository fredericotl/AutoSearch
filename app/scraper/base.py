from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from app.core import ScraperUnavailable, ProductGone, ScraperBlocked
import requests

class Scraper(ABC):
    HEADER = {"Accept-Language": "pt-BR,pt-PT;q=0.9,pt-AO;q=0.8,pt;q=0.7,en-US;q=0.6,en;q=0.5",
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
              "Accept-encoding": "gzip, deflate",
              "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
              "sec-ch-ua-mobile": "?0","sec-ch-ua-platform": '"Windows"',"sec-fetch-dest": "document",
              "sec-fetch-mode": "navigate","sec-fetch-site": "none","sec-fetch-user": "?1",
              }
    TIMEOUT = 10

    def __init__(self):
        self.session = requests.Session()
        self._warm_up(self.session)
    def get_soup(self, url):
        try:
            response = self.session.get(url, headers=self.HEADER, timeout=self.TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise ScraperUnavailable(f"{type(e).__name__}: {e}") from e
        status = response.status_code
        if status == 404: #Pagina não existe mais
            raise ProductGone(f"Status {status}; URL: {url}")
        if status in (403, 503): #Trava de acesso antibot
            # TODO lidar com trava
            raise ScraperBlocked(f"Status {status}; URL: {url}")
        if not response.ok: # Qualquer outro erro
            raise ScraperUnavailable(f"Status {status}; URL: {url}")
        soup = BeautifulSoup(response.text, "html.parser")
        if self._is_blocked(soup):
            raise ScraperBlocked(f"Blocked by content check; URL: {url}")
        return soup

    def _is_blocked(self, soup) -> bool:
        return False

    def _warm_up(self, session):
        pass

    @abstractmethod
    def parse(self, soup:BeautifulSoup)-> int | None:
        pass

    def get_price(self, url):
        soup = self.get_soup(url)
        return self.parse(soup)


