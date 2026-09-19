from app.db import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from app.core import now

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price = Column(Integer)
    captured_at = Column(DateTime, default=now, nullable=False)

    __table_args__ = (
        Index('ix_product_captured', 'product_id', 'captured_at'),
    )