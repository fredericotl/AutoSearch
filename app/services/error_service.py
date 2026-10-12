from app.schemas import  CreateError
from app.models import  Error
from sqlalchemy.orm import Session


def save_error(db:Session, error: CreateError):
    error_model = Error(**error.model_dump())
    db.add(error_model)

def has_open_error(db: Session, error: CreateError) -> bool:
    open_error = db.query(Error).filter(Error.source == error.source,
                                        Error.error_type == error.error_type,
                                        Error.message == error.message,
                                        Error.is_fixed.is_(False)).first()
    return open_error is not None