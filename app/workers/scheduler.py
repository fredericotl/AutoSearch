from apscheduler.schedulers.background import BackgroundScheduler

class TaskScheduler:

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def add_daily(self, job, hour: int):
        self.scheduler.add_job(job, "cron", hour= hour)

    def start(self):

        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()