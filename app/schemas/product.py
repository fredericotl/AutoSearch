from pydantic import BaseModel, Field, HttpUrl,ConfigDict
from typing import Optional
from app.schemas.user import ViewerRef
from enum import Enum

class ProductPriceStatus(str, Enum):
    FROM_DB = "from_db"
    SCRAPED = "scraped"
    NO_PRICE_FOUND = "no_price_found"

class CreateProduct(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    link: HttpUrl
    specification: Optional[str] = Field(None, max_length=1000)

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    link: str
    specification: str | None
    price_today: str | None = None
    lowest_price: str | None = None
    mean: str | None = None

class WatchedProductsResponse(BaseModel):
    products: list[ProductResponse]

class CreateProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    link: str
    specification: str | None

class ProductPriceResponse(BaseModel):
    title: str | None
    price: int | None
    link: str
    status: ProductPriceStatus

class ProductToScrape(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    link: str
    viewers: list[ViewerRef]
