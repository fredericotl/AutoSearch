from datetime import datetime
from app.core.config import settings
from zoneinfo import ZoneInfo

def now():
    time_zone = ZoneInfo(settings.time_zone)
    now_aware= datetime.now(tz=time_zone)
    now_naive = now_aware.replace(tzinfo=None)
    return now_naive