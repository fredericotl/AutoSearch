from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import PriceHistory
from app.schemas import ProductPriceResponse, PriceWindowStats, Criteria, ProductToScrape
from datetime import date, timedelta, datetime, time
from app.scraper import get_scraper_for_link
from app.core.exeptions import PriceNotFound

WINDOW_OF_DAYS = 365
MINIMUM_DATA_COUNT = 7

#TODO resolve possiveis redundancias de busca de preços ou coisas do tipo
def _find_product_price_by_date(db: Session, product_id: int, check_date: date):
    product_price = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        func.date(PriceHistory.captured_at) == check_date).first()
    if product_price:
        return  product_price.price
    return None

def _capture_price(db: Session, product_model: ProductToScrape) -> ProductPriceResponse:
    today = date.today()

    product_price_today = _find_product_price_by_date(db, product_model.id, today)
    if product_price_today:
        return ProductPriceResponse(title=product_model.title, price=product_price_today,
                                     link=product_model.link, status="from_db")

    scraper = get_scraper_for_link(product_model.link)
    price = scraper.get_price(product_model.link)

    product_price_model = PriceHistory(product_id=product_model.id, price=price)
    db.add(product_price_model)
    db.commit()
    db.refresh(product_price_model)

    return ProductPriceResponse(title=product_model.title, price=price, link=product_model.link,
                                 status="scraped" if price else "no_price_found")


def save_product_price_api(db: Session, product_model: ProductToScrape) -> ProductPriceResponse:
    return _capture_price(db, product_model)


def save_product_price_scheduler(db: Session, product_model: ProductToScrape) -> int:
    result = _capture_price(db, product_model)
    if result.status == "no_price_found":
        raise PriceNotFound("Price Not Found")
    return result.price

def get_price_window_stats(db: Session, product_id: int, window: int = WINDOW_OF_DAYS)-> PriceWindowStats:
    today = datetime.combine(date.today(), time.min)
    start = today - timedelta(days=window)
    stats = db.query(
        func.min(PriceHistory.price).label("minimum"), func.count(PriceHistory.price).label("count")
    ).filter(PriceHistory.product_id == product_id,
             PriceHistory.captured_at >= start,
             PriceHistory.captured_at < today).one()
    return PriceWindowStats(minimum=stats.minimum,
                            count=stats.count)

#TODO Add outros critérios aqui
def evaluate_price_criteria(price_today: int, price_stats: PriceWindowStats,
                            minimum_data_count: int = MINIMUM_DATA_COUNT)-> Criteria | None:
    if price_stats.minimum is None:
        return None
    if (price_stats.count >= minimum_data_count) and price_today < price_stats.minimum:
        return Criteria.LOWEST_PRICE
    return None




