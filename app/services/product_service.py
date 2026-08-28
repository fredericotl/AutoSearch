from sqlalchemy.orm import Session,selectinload
from app.models import Product, User
from app.services.detection_service import remove_detections
from app.schemas import CreateProduct
from app.core.exceptions import ProductNotFound, UserNotFollow

def get_watched_products(db: Session, user_id: int):
    user = db.get(User, user_id)
    return user.watching

def get_all_products(db: Session):
    return db.query(Product).options(selectinload(Product.viewers)).all()

def get_product(db: Session, product_id: int)-> type[Product]|None:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFound(f"Product Not Found")
    return product

def get_product_viewers(db: Session, product_id: int) -> list[type[User]]|None:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFound(f"Product Not Found")
    viewers = []
    for viewer in product.viewers:
        viewers.append(viewer)
    return viewers


#TODO lidar com links repetidos, escolher se associa a um produto já existente ou apenas informa que existe
def create_product(db: Session, product_request: CreateProduct, user_id: int):
    owner = db.get(User, user_id)
    product_model = Product(title=product_request.title,
                            link=str(product_request.link),
                            specification=product_request.specification,
                            owner_id=user_id,
                            viewers=[owner])
    db.add(product_model)
    db.commit()
    db.refresh(product_model)
    return product_model

#TODO Resolver quem é o novo dono lidar com exceptions
def remove_product(db:Session, product_model: Product, user_id: int):
    user = db.get(User, user_id)
    viewers = product_model.viewers
    if user not in viewers:
        raise UserNotFollow("User Do Not Follow Product")
    if len(viewers) == 1:
        remove_detections(db, product_model.id)
        db.delete(product_model)
    else:
        product_model.viewers.remove(user)
        if product_model.owner_id == user_id:
            product_model.owner_id = None
    db.commit()






