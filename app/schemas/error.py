from pydantic import BaseModel
from enum import Enum

class ErrorSource(str, Enum):
    SCRAPER = "scraper"
    NOTIFIER = "notifier"

class CreateError(BaseModel):

    source: ErrorSource
    error_type: str
    message: str | None = None
    product_id: int | None = None
    user_id: int | None = None