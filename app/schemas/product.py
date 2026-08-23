from pydantic import BaseModel, Field, HttpUrl,ConfigDict
from typing import Optional, Literal
from app.schemas.user import ViewerRef

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

class ProductPriceResponse(BaseModel):
    title: str | None
    price: int | None
    link: str
    status: Literal["from_db","scraped","no_price_found"]

class ProductToScrape(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    link: str
    viewers: list[ViewerRef]
