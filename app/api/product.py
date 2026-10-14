from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, Path, HTTPException, APIRouter
from starlette import status
from app.core import (get_current_user, ScraperFail, ProductNotFound, UserNotFollow, UnsupportedScraper, UserNotFound,
                      UserAlreadyFollow, ProductAlreadyExists)
from app.db import get_db
from app.schemas import (CreateProduct, CreateProductResponse,
                         ProductResponse, ProductPriceResponse, ProductToScrape, WatchedProductsResponse)
from app.services import (get_product, get_watched_products_with_prices, get_product_with_prices,
                          create_product, unfollow_product_service, save_product_price_api, follow_product_service)
router = APIRouter(prefix="/products", tags=["Products"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK, response_model=WatchedProductsResponse)
async  def read_all(user: user_dependency, db: db_dependency):
    try:
        products = get_watched_products_with_prices(db, user.get("id"))
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))
    return products

@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def read_product(user: user_dependency, db: db_dependency, product_id: int = Path(gt=0)):
    try:
        return get_product_with_prices(db, product_id)
    except ProductNotFound as e:
        raise HTTPException(status_code=404, detail= str(e))

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CreateProductResponse)
async  def create_new_product(user: user_dependency, db: db_dependency, product_request: CreateProduct):
    try:
        product = create_product(db, product_request, user.get("id"))
    except ProductAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))
    db.commit()
    return product

@router.post("/{product_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def follow_product(user: user_dependency, db: db_dependency, product_id : int =Path(gt=0)):
    try:
        follow_product_service(db, product_id, user.get("id"))
        db.commit()
    except ProductNotFound as e:
        raise HTTPException(404, str(e))
    except UserAlreadyFollow as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))

##TODO Pensar em formas de fazer update do produto se é coerente talvez no processo de validação

@router.post("/{product_id}/unfollow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_product(user: user_dependency, db: db_dependency, product_id : int =Path(gt=0)):
    try:
        unfollow_product_service(db, product_id, user.get("id"))
        db.commit()
    except ProductNotFound as e:
        raise HTTPException(404, str(e))
    except UserNotFollow as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/{product_id}/save-price", status_code=status.HTTP_201_CREATED, response_model=ProductPriceResponse)
async  def update_product_price(user: user_dependency, db: db_dependency, product_id: int):
    try:
        product = get_product(db, product_id)
        product_model = ProductToScrape.model_validate(product)
        product = save_product_price_api(db, product_model)
        db.commit()
        return product
    except ProductNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnsupportedScraper as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ScraperFail as e:
        raise HTTPException(status_code=500, detail=str(e))




