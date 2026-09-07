from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.models import PriceHistory
from app.schemas import ProductPriceResponse, ProductToScrape
from app.services.price_window import PriceWindow
from datetime import date, timedelta, datetime, time
from app.scraper import get_scraper_for_link
from app.core import PriceNotFound, now, settings
from dataclasses import dataclass, field

@dataclass
class PriceInfo:
    lowest_price: str | None
    mean: str | None

@dataclass
class ProductPrices:
    history: list[int] = field(default_factory=list)
    price_today: int | None = None


#TODO resolve possiveis redundancias de busca de preços ou coisas do tipo
def _product_price_by_date(db: Session, product_id: int, check_date: date):
    product_price = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        func.date(PriceHistory.captured_at) == check_date).first()
    if product_price:
        return  product_price.price
    return None

def _capture_price(db: Session, product_model: ProductToScrape) -> ProductPriceResponse:
    today = date.today()

    product_price_today = _product_price_by_date(db, product_model.id, today)
    if product_price_today:
        return ProductPriceResponse(title=product_model.title, price=product_price_today,
                                     link=product_model.link, status="from_db")

    scraper = get_scraper_for_link(product_model.link)
    price = scraper.get_price(product_model.link)

    product_price_model = PriceHistory(product_id=product_model.id, price=price)
    db.add(product_price_model)

    return ProductPriceResponse(title=product_model.title, price=price, link=product_model.link,
                                 status="scraped" if price else "no_price_found")


def save_product_price_api(db: Session, product_model: ProductToScrape) -> ProductPriceResponse:
    result = _capture_price(db, product_model)
    return result

def save_product_price_scheduler(db: Session, product_model: ProductToScrape) -> int:
    result = _capture_price(db, product_model)
    if result.status == "no_price_found":
        raise PriceNotFound("Price Not Found")
    return result.price

def price_str(price: int, currency:str = "R$ ")-> str:
    units, cents = divmod(price, 100)
    units = f"{units:,}".replace(",", ".")
    return f"{currency}{units},{cents:02d}"

def get_prices_by_products(db: Session, product_ids: set[int])-> dict[int, ProductPrices]:
    window_of_days = settings.window_of_days
    today = now().date()
    start = datetime.combine(today, time.min) - timedelta(days=window_of_days)
    query = select(PriceHistory.product_id, PriceHistory.price, PriceHistory.captured_at) \
            .where(PriceHistory.product_id.in_(product_ids),
                   PriceHistory.price.is_not(None),
                   PriceHistory.captured_at >= start)
    rows = db.execute(query).fetchall()
    prices = {product_id: ProductPrices() for product_id in product_ids}
    for product_id, price, captured_at in rows:
        prices[product_id].history.append(price)
        if captured_at.date() == today:
            prices[product_id].price_today = price
    return prices

def build_price_info(prices:list[int]) -> PriceInfo:
    window = PriceWindow.from_prices(prices=prices)
    lowest_price = window.minimum
    mean = window.mean()
    if lowest_price is not None:
        lowest_price = price_str(lowest_price)
        mean = price_str(int(mean))
    return PriceInfo(lowest_price=lowest_price, mean=mean)