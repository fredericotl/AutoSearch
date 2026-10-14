from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core import now
from app.models import Detection, Product, User
from app.schemas import DetectionNotifyByUser, DetectedProduct, NotifierInput
from datetime import timedelta

NOTIFICATION_COOLDOWN = timedelta(days=7)

def _is_detection_pertinent(price_today: int, last_notification):
    if last_notification is None:
        return True
    last_price = last_notification.price
    send_at_delta = now().date() - last_notification.sent_at.date()
    if last_price > price_today:
        return True
    elif send_at_delta >= NOTIFICATION_COOLDOWN:
        return True
    return False

def _get_pendent_detections(db: Session, product: DetectedProduct, user_id: int):
    return db.query(Detection).filter(Detection.product_id == product.id,
                                      Detection.user_id == user_id,
                                     Detection.sent_at.is_(None)).first()

def create_detections(db: Session, product: DetectedProduct):

    position = func.row_number().over(partition_by=Detection.user_id, order_by=(Detection.sent_at.desc(), Detection.id.desc())).label("position")
    by_product = select(Detection.user_id, Detection.price, Detection.sent_at ,position) \
        .where(Detection.product_id == product.id,
               Detection.sent_at.is_not(None)).subquery()
    by_position = db.execute(select(by_product).where(by_product.c.position == 1)).all()
    by_user = {row.user_id: row for row in by_position}
    for viewer in product.viewers:
        pendent_detection = _get_pendent_detections(db, product, viewer.id)
        if pendent_detection:
            pendent_detection.price = product.price
            pendent_detection.criteria = product.criteria
            pendent_detection.detected_at = now()
            continue
        last_notification = by_user.get(viewer.id)
        if not _is_detection_pertinent(price_today=product.price, last_notification=last_notification):
            continue
        detection_model = Detection(product_id=product.id,
                                    user_id=viewer.id,
                                    criteria=product.criteria,
                                    price=product.price,
                                    )
        db.add(detection_model)

def get_pendent_detections_by_user(db: Session)-> list[NotifierInput]:
    detections = (db.query(Detection.id, Detection.user_id, Detection.price, Detection.criteria,
                          Product.title, Product.link,
                          User.email, User.first_name)
                  .join(Product, Detection.product_id == Product.id)
                  .join(User, Detection.user_id == User.id)
                  .filter(Detection.sent_at.is_(None)).all())
    grouped: dict[tuple[int, str, str], list[DetectionNotifyByUser]] = {}
    for detection in detections:
        item = DetectionNotifyByUser(detection_id= detection.id,
                                        title= detection.title,
                                        link= detection.link,
                                        price= detection.price,
                                        criteria= detection.criteria
                                        )
        grouped.setdefault((detection.user_id, detection.email,detection.first_name), []).append(item)
    list_notifiers = []
    for (user_id, email, name), items in grouped.items():
        list_notifiers.append(NotifierInput(user_id=user_id, user_email=email, user_name=name, items=items, ))
    return list_notifiers

def mark_detections_sent(db:Session, list_detections: list[DetectionNotifyByUser]):
    if len(list_detections) == 0:
        return
    list_id = [ d.detection_id for d in list_detections]
    (db.query(Detection).filter(Detection.sent_at.is_(None),Detection.id.in_(list_id))
                  .update({Detection.sent_at: now()}, synchronize_session=False))

def remove_detections(db:Session, product_id: int):
    db.query(Detection).filter(Detection.product_id == product_id).delete()

def discard_outdated_pendent_detections(db: Session, product_id: int, price_today: int):
    db.query(Detection).filter(Detection.product_id == product_id,
                               Detection.sent_at.is_(None),
                               Detection.price < price_today).delete()