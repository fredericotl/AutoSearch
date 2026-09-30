from app.scraper.factory import get_scraper_for_link

def test_factory_reuses_scraper_for_same_site():
    a = get_scraper_for_link("https://www.amazon.com.br/dp/X")
    b = get_scraper_for_link("https://a.co/d/Y")
    assert a is b