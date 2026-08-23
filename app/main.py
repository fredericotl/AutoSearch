from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import auth, users, product
from app.workers.scraper_task import ScraperTask
from app.workers.notifier_task import NotifierTask
from app.workers.scheduler import TaskScheduler
import app.models
from app.db.session import Base, engine

HOUR = 3

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scraper = ScraperTask()
    notifier = NotifierTask()

    def daily_round():
        try:
            scraper.run()
        finally:
            notifier.run()

    scheduler = TaskScheduler()
    scheduler.add_daily(daily_round,HOUR)
    scheduler.start()
    yield
    scheduler.stop()

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(product.router)