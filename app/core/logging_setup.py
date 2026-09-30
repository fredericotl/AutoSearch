import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from logging.handlers import TimedRotatingFileHandler
from app.core.config import settings, BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "datetime: %(asctime)s - level: %(levelname)s - name: %(name)s - message: %(message)s"
LOG_BACKUP_WEEKS = 4

_configured = False

def _to_local_time(seconds: float):
    zone = ZoneInfo(settings.time_zone)
    return datetime.fromtimestamp(seconds, tz=zone).timetuple()

def setup_logging() -> None:
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = TimedRotatingFileHandler(LOG_FILE, when="W5",
                                       backupCount=LOG_BACKUP_WEEKS, encoding="utf-8")
    formatter = logging.Formatter(LOG_FORMAT)
    formatter.converter = _to_local_time
    handler.setFormatter(formatter)

    app_logger = logging.getLogger("app")
    app_logger.setLevel(settings.log_level)
    app_logger.addHandler(handler)

    scheduler_logger = logging.getLogger("apscheduler")
    scheduler_logger.setLevel(logging.INFO)
    scheduler_logger.addHandler(handler)

    _configured = True
