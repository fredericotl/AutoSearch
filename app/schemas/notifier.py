from pydantic import BaseModel,  HttpUrl, EmailStr, Field
from enum import Enum
from app.schemas.user import ViewerRef

class Criteria(str, Enum):
    LOWEST_PRICE = "lowest_price"
    # THRESHOLD = "threshold" #TODO avaliar possível implementação
    # ANOMALY = "anomaly" #TODO construir lógica apos significância estatística pós MVP

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
    itens: list[DetectionNotifyByUser]

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

#TODO definir resposta para outros critérios
class PriceWindowStats(BaseModel):
    minimum: int | None
    count: int