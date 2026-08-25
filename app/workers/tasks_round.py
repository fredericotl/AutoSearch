from app.workers.notifier_task import NotifierTask
from app.workers.scraper_task import ScraperTask
import logging
import time

logger = logging.getLogger(__name__)


class TasksRound:
    def __init__(self):
        self.scraper = ScraperTask()
        self.notifier = NotifierTask()

    def run(self):
        start = time.perf_counter()
        logger.info("round started")
        try:
            self.scraper.run()
        except Exception:
            duration = time.perf_counter() - start
            logger.exception("round interrupted after %.2fs", duration)
            raise
        finally:
            self.notifier.run()
            duration = time.perf_counter() - start
            logger.info("round ended after %.2fs", duration)




