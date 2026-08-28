import logging
from app.core.config import settings,BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "datetime: %(asctime)s - level: %(levelname)s - name: %(name)s - message: %(message)s"

_configured = False

def setup_logging() -> None:
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    app_logger = logging.getLogger("app")
    app_logger.setLevel(settings.log_level)
    app_logger.addHandler(handler)

    scheduler_logger = logging.getLogger("apscheduler")
    scheduler_logger.setLevel(logging.INFO)
    scheduler_logger.addHandler(handler)

    _configured = True
