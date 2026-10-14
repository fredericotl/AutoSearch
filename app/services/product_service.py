from sqlalchemy.orm import Session,selectinload
from app.core.exceptions import ProductAlreadyExists, UserAlreadyFollow
from app.models import Product
from app.services.detection_service import remove_detections
from app.services.user_service import find_user
from app.services.price_service import price_str, get_prices_by_products, build_price_info, ProductPrices
from app.schemas import CreateProduct, ProductResponse, WatchedProductsResponse
from app.core import ProductNotFound, UserNotFollow

def get_watched_products(db: Session, user_id: int):
    user = find_user(db, user_id)
    return user.watching

def get_all_products(db: Session):
    return db.query(Product).options(selectinload(Product.viewers)).where(Product.is_search_active == True).all()

def get_product_by_link(db: Session, link: str)-> Product|None:
    product = db.query(Product).filter(Product.link == link).first()
    return product

def get_product(db: Session, product_id: int)-> Product:
    product = db.get(Product, product_id)
    if not product:
        raise ProductNotFound(f"Product Not Found")
    return product

def _get_product_response(prices: dict[int, ProductPrices], product: Product) -> ProductResponse:
    price_today = prices[product.id].price_today
    if price_today is not None:
        price_today = price_str(price_today)
    price_info = build_price_info(prices=prices[product.id].history)
    lowest_price = price_info.lowest_price
    mean = price_info.mean
    product_response = ProductResponse(id=product.id,
                                       title=product.title,
                                       link=product.link,
                                       specification=product.specification,
                                       price_today=price_today,
                                       lowest_price=lowest_price,
                                       mean=mean)
    return product_response

def get_product_with_prices(db: Session, product_id: int)-> ProductResponse:
    product = get_product(db, product_id)
    prices = get_prices_by_products(db, {product_id})
    product_response = _get_product_response(prices, product)
    return product_response

def get_watched_products_with_prices(db: Session, user_id: int)-> WatchedProductsResponse:
    products = get_watched_products(db= db, user_id=user_id)
    product_ids = {p.id for p in products}
    all_prices = get_prices_by_products(db=db, product_ids=product_ids)
    products_list = []
    for product in products:
        product_response = _get_product_response(prices=all_prices, product=product)
        products_list.append(product_response)
    return WatchedProductsResponse(products=products_list)

def create_product(db: Session, product_request: CreateProduct, user_id: int):
    db_product = get_product_by_link(db, str(product_request.link))
    if db_product:
        raise ProductAlreadyExists(f"Product already exists, follow the product with id {db_product.id}")
    owner = find_user(db, user_id)
    product_model = Product(title=product_request.title,
                            link=str(product_request.link),
                            specification=product_request.specification,
                            owner_id=user_id,
                            viewers=[owner])
    db.add(product_model)
    return product_model

def follow_product_service(db:Session, product_id: int, user_id: int):
    product_model = get_product(db, product_id)
    user = find_user(db, user_id)
    viewers = product_model.viewers
    if user in viewers:
        raise UserAlreadyFollow("User Already Follow Product")
    product_model.is_search_active = True
    product_model.viewers.append(user)
    db.add(product_model)


def unfollow_product_service(db:Session, product_id: int, user_id: int):
    product = get_product(db, product_id)
    user = find_user(db, user_id)
    viewers = product.viewers
    if user not in viewers:
        raise UserNotFollow("User Do Not Follow Product")
    product.viewers.remove(user)
    if len(viewers) == 0:
        product.is_search_active = False
    else:
        if product.owner_id == user_id:
            product.owner_id = None

def delete_product(db:Session, product_model: Product):
    remove_detections(db, product_model.id)
    db.delete(product_model)






