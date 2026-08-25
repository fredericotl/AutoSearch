from app.workers import TasksRound
from app.core.logging_setup import setup_logging

setup_logging()
TasksRound().run()