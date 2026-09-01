from app.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.associations import product_viewers



class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String,nullable=False)
    link = Column(String, nullable=False)
    specification = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete= "SET NULL"), nullable=True)
    is_search_active = Column(Boolean, default=True )
    viewers = relationship("User", secondary=product_viewers, back_populates="watching")

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_products"
    )

