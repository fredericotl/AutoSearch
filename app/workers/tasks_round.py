from app.workers.notifier_task import NotifierTask
from app.workers.scraper_task import ScraperTask



class TasksRound:
    def __init__(self):
        self.scraper = ScraperTask()
        self.notifier = NotifierTask()

    def run(self):
        try:
            self.scraper.run()
        finally:
            self.notifier.run()

if __name__ == "__main__":
    TasksRound().run()


