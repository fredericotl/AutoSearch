import logging
from pathlib import Path
from app.core.config import settings


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "datetime: %(asctime)s - level: %(levelname)s - name: %(name)s - message: %(message)s"

_configured = False

def setup_logging() -> None:
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("app")
    logger.setLevel(settings.log_level)

    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.addHandler(handler)
    _configured = True
