from app.db import Base
from sqlalchemy import Column, ForeignKey, Table


product_viewers = Table(
    "product_viewers",
    Base.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)