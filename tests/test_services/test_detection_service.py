from app.services.detection_service import (create_detections, get_pendent_detections_by_user,
                                            mark_detections_sent, _is_detection_pertinent)
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from app.schemas import DetectionNotifyByUser, DetectedProduct
from app.schemas.price import Criteria
from types import SimpleNamespace
from datetime import timedelta
from app.core import now

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def mock_detection_product(n:int = 1):
    mock_product = MagicMock(spec=DetectedProduct)
    mock_product.id = n
    mock_product.title = f"Test Product {n}"
    mock_product.price = 100
    mock_product.link = f"http://example.com/product/{n}"
    mock_product.viewers = [MagicMock(id=1), MagicMock(id=2)]
    mock_product.criteria = Criteria.LOWEST_PRICE
    return mock_product

def mock_detection_row(id: int = 1, user_id: int = 10):
    row = SimpleNamespace(
        id=id, user_id=user_id, price=9999, criteria=Criteria.LOWEST_PRICE,
        title="Notebook", link=f"http://example.com/product/{id}",
        email=f"user@example.com", first_name=f"testuser")
    return row

def test_is_detection_pertinent():
    assert _is_detection_pertinent(100, None)
    last_notification = MagicMock()
    last_notification.price = 100
    last_notification.sent_at = now() - timedelta(days=3)
    assert _is_detection_pertinent(99, last_notification)
    assert not _is_detection_pertinent(100, last_notification)
    last_notification.sent_at = now() - timedelta(days=7)
    assert _is_detection_pertinent(100, last_notification)
    last_notification.sent_at = now() - timedelta(days=6)
    assert not _is_detection_pertinent(100, last_notification)

def test_create_detections():
    db = mock_db_session()
    db.query.return_value.filter.return_value.first.return_value = None
    product = mock_detection_product()
    create_detections(db, product)
    assert db.add.call_count == len(product.viewers)


def test_create_detections_updates_pendent():
    db = mock_db_session()
    pendent = MagicMock()
    pendent.price = 9999
    pendent.criteria = None
    pendent.detected_at = None
    db.query.return_value.filter.return_value.first.return_value = pendent
    product = mock_detection_product()
    create_detections(db, product)
    assert db.add.call_count == 0
    assert pendent.price == product.price
    assert pendent.criteria == product.criteria
    assert pendent.detected_at.date() == now().date()

def test_get_pendent_detections_by_user_one_item():
    db = mock_db_session()
    row1 = mock_detection_row(1,10)
    row2 = mock_detection_row(2,10)
    row3 = mock_detection_row(3,20)

    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [row1]

    result = get_pendent_detections_by_user(db)
    assert len(result) == 1
    assert result[0].user_id == row1.user_id

    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [row1, row2]
    result = get_pendent_detections_by_user(db)
    assert len(result) == 1

    db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [row1, row2, row3]
    result = get_pendent_detections_by_user(db)
    assert len(result) == 2
    assert result[0].user_id == 10
    assert result[1].user_id == 20

def test_mark_detections_sent_not_empty():
    db = mock_db_session()
    detections = [DetectionNotifyByUser(detection_id=1, title="Notebook", link="http://example.com/product/1",
                                        price=9999, criteria=Criteria.LOWEST_PRICE)]
    mark_detections_sent(db, detections)
    db.query.return_value.filter.return_value.update.assert_called_once()

def test_mark_detections_sent_empty():
    db = mock_db_session()
    mark_detections_sent(db, [])
    db.query.assert_not_called()