from app.services import (get_all_products, save_product_price_scheduler, save_error,create_detections, PriceWindow)
from app.db import SessionLocal
from app.schemas import CreateError, DetectedProduct, ProductToScrape, ErrorSource
from time import sleep
from app.core import (ScraperFail, UnsupportedScraper, PriceNotFound, ScraperBlocked,
                                 ScraperUnavailable, ProductGone)
from sqlalchemy.orm import Session

class ScraperTask:
    WAIT = 1

    def _get_all_products(self):
        db = SessionLocal()
        try:
            products =  get_all_products(db)
            return [ProductToScrape.model_validate(p) for p in products]

        finally:
            db.close()

    def _save_error(self, db: Session, error: ScraperFail, product: ProductToScrape ):
        error_data = CreateError(
            product_id=product.id,
            error_type=type(error).__name__,
            source=ErrorSource.SCRAPER,
            message=str(error),
        )
        save_error(db, error_data)


    def run(self):
        all_products = self._get_all_products()
        for product in all_products:
            db = SessionLocal()
            try:
                window = PriceWindow.from_history(db, product.id)
                price_today = save_product_price_scheduler(db, product)
                db.commit()
                criteria = window.evaluate_price_criteria(price_today)
                if criteria is not None:
                    product_to_notify = DetectedProduct(
                        id= product.id,
                        title= product.title,
                        price= price_today,
                        link= product.link,
                        viewers= product.viewers,
                        criteria= criteria
                    )
                    create_detections(db, product_to_notify)
                    db.commit()
            # TODO identificar site para não repetir mesmo erro
            except (ScraperUnavailable, ProductGone, UnsupportedScraper, ScraperBlocked, PriceNotFound) as e:
                self._save_error(db, e,product)
                db.commit()
            except ScraperFail as e:
                self._save_error(db, e,product)
                db.commit()
            finally:
                db.close()
            sleep(self.WAIT)



