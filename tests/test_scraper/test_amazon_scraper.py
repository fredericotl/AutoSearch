from bs4 import BeautifulSoup
from app.scraper.amazon_scraper import AmazonScraper

MAIN_PRICE = (
    '<div id="corePrice_feature_div">'
    '<span class="a-price apex-pricetopay-value">'
    '<span class="a-offscreen">{}</span>'
    '</span></div>'
)

CAROUSEL_PRICE = (
    '<div id="desktop-dp-lpo_feature_div_0">'
    '<span class="a-price"><span class="a-offscreen">R$69,49</span></span>'
    '</div>'
)

def make_soup(html):
    return BeautifulSoup(html, "html.parser")

def test_parse_price():
    soup = make_soup(MAIN_PRICE.format("R$ 1.234,56"))
    assert AmazonScraper().parse(soup) == 123456

def test_parse_ignores_carousel_when_product_unavailable():
    soup = make_soup(CAROUSEL_PRICE)
    assert AmazonScraper().parse(soup) is None

def test_parse_prefers_main_price_over_carousel():
    soup = make_soup(CAROUSEL_PRICE + MAIN_PRICE.format("R$ 462,10"))
    assert AmazonScraper().parse(soup) == 46210

def test_parse_empty_offscreen_returns_none():
    soup = make_soup(MAIN_PRICE.format(" "))
    assert AmazonScraper().parse(soup) is None

def test_parse_price_none():
    html = '<div></div>'
    soup = BeautifulSoup(html, "html.parser")
    assert AmazonScraper().parse(soup) is None