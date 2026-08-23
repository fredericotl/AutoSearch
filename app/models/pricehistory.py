from app.db.session import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Index



#TODO status de falha e lidar quando produto apagar
class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Integer)
    captured_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_product_captured', 'product_id', 'captured_at'),
    )