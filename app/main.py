from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import auth, users, product
from app.workers import TasksRound, TaskScheduler
from app.core.logging_setup import setup_logging
import app.models
from app.db.session import Base, engine


HOUR = 3

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    round = TasksRound()
    scheduler = TaskScheduler()
    scheduler.add_daily(round.run,HOUR)
    scheduler.start()
    yield
    scheduler.stop()

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(product.router)