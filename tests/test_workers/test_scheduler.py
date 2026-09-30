from app.core.config import settings
from app.workers.scheduler import TaskScheduler

def test_daily_job_uses_configured_time_zone(monkeypatch):
    monkeypatch.setattr(settings, "time_zone", "Asia/Tokyo")
    scheduler = TaskScheduler()
    scheduler.add_daily(lambda: None, hour=3)
    job = scheduler.scheduler.get_jobs()[0]
    assert str(job.trigger.timezone) == "Asia/Tokyo"