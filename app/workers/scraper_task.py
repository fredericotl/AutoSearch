from app.services import (get_all_products, save_product_price_scheduler, save_error, create_detections, PriceWindow,
                          has_open_error, discard_outdated_pendent_detections)
from app.db import SessionLocal
from app.schemas import CreateError, DetectedProduct, ProductToScrape, ErrorSource
from time import sleep
from app.core import ScraperFail
import logging
from time import perf_counter
import random

logger = logging.getLogger(__name__)
class ScraperTask:
    WAIT_MIN, WAIT_MAX = 1, 2

    def _get_all_products(self):
        db = SessionLocal()
        try:
            products =  get_all_products(db)
            return [ProductToScrape.model_validate(p) for p in products]

        finally:
            db.close()

    def _build_error(self, error: Exception, product: ProductToScrape) -> CreateError:
        return CreateError(
            product_id=product.id,
            error_type=type(error).__name__,
            source=ErrorSource.SCRAPER,
            message=str(error),
        )


    def run(self):
        all_products = self._get_all_products()
        round_start = perf_counter()
        failed = 0
        logger.info("scraping %d products", len(all_products))
        for product in all_products:
            db = SessionLocal()
            start = perf_counter()
            outcome = "unexpected"
            try:
                window = PriceWindow.from_history(db, product.id)
                price_today = save_product_price_scheduler(db, product)
                discard_outdated_pendent_detections(db, product.id, price_today)
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
                outcome = "ok"
            except ScraperFail as e:
                save_error(db, self._build_error(e, product))
                db.commit()
                outcome = type(e).__name__
                failed += 1
            except Exception as e:
                logger.exception("product %s: unexpected error", product.id)
                db.rollback()
                error_data = self._build_error(e, product)
                if not has_open_error(db, error_data):
                    save_error(db, error_data)
                    db.commit()
                outcome = type(e).__name__
                failed += 1
            finally:
                db.close()
                level = logging.INFO if outcome == "ok" else logging.WARNING
                logger.log(level, "product %s: %s in %.2fs", product.id, outcome, perf_counter() - start)
            sleep(random.uniform(self.WAIT_MIN, self.WAIT_MAX))

        logger.info("scraping finished: %d products, %d failed, %.2fs",
                    len(all_products), failed, perf_counter() - round_start)



