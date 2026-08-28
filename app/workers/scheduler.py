from apscheduler.schedulers.background import BackgroundScheduler


class TaskScheduler:
    MISFIRE_GRACE_TIME = 3600 #One Hour

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def add_daily(self, job, hour: int, misfire_grace_time: int = MISFIRE_GRACE_TIME):
        self.scheduler.add_job(job, "cron", hour= hour,
                           misfire_grace_time=misfire_grace_time)

    def start(self):

        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()