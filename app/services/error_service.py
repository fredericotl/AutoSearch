from app.schemas import  CreateError
from app.models import  Error
from sqlalchemy.orm import Session


def save_error(db:Session, error: CreateError):
    error_model = Error(**error.model_dump())
    db.add(error_model)
