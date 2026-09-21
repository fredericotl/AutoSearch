from bs4 import BeautifulSoup
from app.scraper.amazon_scraper import AmazonScraper

def test_parse_price():
    html = '<span class="a-offscreen">R$ 1.234,56</span>'
    soup = BeautifulSoup(html, "html.parser")
    assert AmazonScraper().parse(soup) == 123456

def test_parse_price_none():
    html = '<div></div>'
    soup = BeautifulSoup(html, "html.parser")
    assert AmazonScraper().parse(soup) is None