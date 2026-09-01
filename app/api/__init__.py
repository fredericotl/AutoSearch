from app.api.auth import router as auth_router
from app.api.product import router as product_router
from app.api.user import router as user_router

__all__ = ["auth_router", "product_router", "user_router"]