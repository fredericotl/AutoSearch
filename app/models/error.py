from app.db.session import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func, Index





class Error(Base):
    __tablename__ = 'errors'

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    error_type = Column(String, nullable=False)
    message = Column(String, nullable=True)
    captured_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_fixed = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index('ix_errors_source_captured', 'source', 'captured_at'),
        Index('ix_errors_product_captured', 'product_id', 'captured_at'),
    )
