from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, Path, HTTPException, APIRouter
from starlette import status
from app.core.security import get_current_user
from app.core.exeptions import ScraperFail
from app.db.session import get_db
from app.schemas import CreateProduct, ProductResponse, ProductPriceResponse, ProductToScrape
from app.services import get_watched_products, get_product, create_product, remove_product,save_product_price_api
from app.core.exeptions import ProductNotFound, UserNotFollow, UnsupportedScraper
router = APIRouter(prefix="/products", tags=["Products"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

#TODO add response model
@router.get("/", status_code=status.HTTP_200_OK)
async  def read_all(user: user_dependency, db: db_dependency):
    return get_watched_products(db, user.get("id"))

@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def read_product(user: user_dependency, db: db_dependency, product_id: int = Path(gt=0)):
    try:
        return get_product(db, product_id)
    except ProductNotFound as e:
        raise HTTPException(status_code=404, detail= str(e))

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
async  def create_new_product(user: user_dependency, db: db_dependency, product_request: CreateProduct):
    return create_product(db, product_request, user.get("id"))

##TODO pensar em uma forma de fazer update sendo o owner e se faz sentido uma vez que existem folowers

#TODO usar ou não REST Delete
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_product(user: user_dependency, db: db_dependency, product_id : int =Path(gt=0)):
    try:
        product_model = get_product(db,product_id)
        remove_product(db, product_model, user.get("id"))
    except ProductNotFound as e:
        raise HTTPException(404, str(e))
    except UserNotFollow as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{product_id}/save-price", status_code=status.HTTP_201_CREATED, response_model=ProductPriceResponse)
async  def update_product_price(user: user_dependency, db: db_dependency, product_id: int):
    try:
        product = get_product(db, product_id)
        product_model = ProductToScrape.model_validate(product)
        return save_product_price_api(db, product_model)
    except ProductNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnsupportedScraper as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ScraperFail as e:
        raise HTTPException(status_code=500, detail=str(e))




