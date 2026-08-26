from pydantic import BaseModel,  HttpUrl, EmailStr, Field
from app.schemas.price import Criteria
from app.schemas.user import ViewerRef


class DetectionNotifyByUser(BaseModel):
    detection_id: int
    title: str
    link: HttpUrl
    price: int
    criteria: Criteria

class NotifierInput(BaseModel):
    user_id: int
    user_email: EmailStr
    user_name: str = Field(max_length=100)
    items: list[DetectionNotifyByUser]

class NotifierSender(BaseModel):
    sender_email: EmailStr
    sender_password: str =Field(max_length=16, min_length=16)

class ProductToNotify(BaseModel):
    id: int
    title: str
    price: int
    link: HttpUrl
    viewers : list[ViewerRef]
    criteria: Criteria

