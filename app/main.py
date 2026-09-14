from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import auth_router, user_router, product_router
from app.workers import TasksRound, TaskScheduler
from app.core import setup_logging
import app.models
from app.db import Base, engine


HOUR = 3

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    round = TasksRound()
    scheduler = TaskScheduler()
    scheduler.add_daily(round.run,HOUR)
    scheduler.start()
    yield
    scheduler.stop()

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(product_router)