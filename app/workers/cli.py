from app.workers import TasksRound
from app.core import setup_logging

if __name__ == "__main__":
    setup_logging()
    TasksRound().run()