from datetime import datetime, time, timedelta
from app.core import now
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.core.security import bcrypt_context
from app.db import Base
from app.main import app
from app.services.product_service import create_product
from app.schemas.product import CreateProduct
import pytest

from app.models import User, Product, PriceHistory

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       connect_args={"check_same_thread": False},
                       poolclass= StaticPool,
                       )


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield  db
    finally:
        db.close()

def override_get_current_user():
    return {"username": "testuser", "id": 1, "role": "default"}

@pytest.fixture
def test_user():
    user = User(username="testuser",
                 email="testuser@gmail.com",
                 first_name= "Test",
                 last_name= "User",
                 hashed_password= bcrypt_context.hash("12345678"),
                 role="default")
    db= TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()

@pytest.fixture
def test_product(test_user):
    db = TestingSessionLocal()
    product_request = CreateProduct(title="Test Product", specification="This is a test product.", link="http://example.com/test-product")
    product = create_product(db, product_request, test_user.id)
    db.commit()
    yield product
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM products;"))
        connection.commit()

@pytest.fixture
def test_price_history(test_product):
    db = TestingSessionLocal()
    base = datetime.combine(now().date(), time.min)
    def _insert(rows):
        for i, price in enumerate(rows):
            db.add(PriceHistory(product_id=test_product.id,
                                captured_at=base - timedelta(days=i),
                                price=price))
        db.commit()
        return test_product
    return _insert


client = TestClient(app)