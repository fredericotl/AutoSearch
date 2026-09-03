from unittest.mock import MagicMock
from app.services.error_service import save_error
from app.models import  Error
from app.schemas import  CreateError, ErrorSource
from sqlalchemy.orm import Session

def mock_db_session():
    return MagicMock(spec=Session)

def test_save_error():
    db = mock_db_session()
    create_error = CreateError(source= ErrorSource.SCRAPER, error_type="Test Error",
                               message="This is a test error", product_id=1, user_id=1)
    save_error(db, create_error)
    error_arg = db.add.call_args[0][0]
    assert error_arg.source == create_error.source
    assert error_arg.error_type == create_error.error_type
    assert error_arg.message == create_error.message
    assert error_arg.product_id == create_error.product_id
    assert error_arg.user_id == create_error.user_id
