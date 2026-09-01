from app.workers import TasksRound
from app.core import setup_logging

setup_logging()
TasksRound().run()