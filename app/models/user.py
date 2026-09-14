from app.db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.associations import product_viewers

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True,nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    watching = relationship("Product", secondary=product_viewers, back_populates="viewers")
    role = Column(String)

    owned_products = relationship(
        "Product",
        foreign_keys="Product.owner_id",
        back_populates="owner",
    )
