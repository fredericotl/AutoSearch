from app.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from app.core import now

class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete= "SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    criteria = Column(String,nullable=False)
    price = Column(Integer, nullable=False)
    detected_at = Column(DateTime, default=now, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    __table_args__ = (
        Index('ix_detections_sent_at', 'sent_at'),
    )