from sqlalchemy.orm import Session
from app.core.clock import now
from app.models import Detection, Product, User
from app.schemas import DetectionNotifyByUser, ProductToNotify, NotifierInput


def create_detections(db: Session, product: ProductToNotify):
    for viewer in product.viewers:
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