from sqlalchemy.orm import Session,selectinload
from app.models import Product, User
from app.services.detection_service import remove_detections
from app.schemas import CreateProduct, ProductResponse, WatchedProductsResponse
from app.core import ProductNotFound, UserNotFollow
from app.services.price_service import price_str, get_prices_by_products, build_price_info, ProductPrices

def get_watched_products(db: Session, user_id: int):
    user = db.get(User, user_id)
    return user.watching

def get_all_products(db: Session):
    return db.query(Product).options(selectinload(Product.viewers)).where(Product.is_search_active == True).all()

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

#TODO lidar com links repetidos, escolher se associa a um produto já existente ou apenas informa que existe
def create_product(db: Session, product_request: CreateProduct, user_id: int):
    owner = db.get(User, user_id)
    product_model = Product(title=product_request.title,
                            link=str(product_request.link),
                            specification=product_request.specification,
                            owner_id=user_id,
                            viewers=[owner])
    db.add(product_model)
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







