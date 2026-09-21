from app.core import get_current_user
from app.db import get_db
from tests.test_api.utils import *

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_create_product(test_user):
    response = client.post("/products/", json={
        "title": "Test Product",
        "specification": "This is a test product.",
        "link": "http://example.com/test-product"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Product"

def test_read_all_products(test_product, test_user):
    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) == 1
    assert data["products"][0]["title"] == "Test Product"
    assert data["products"][0]["specification"] == "This is a test product."

def test_read_product(test_user, test_product):
    response = client.get(f"/products/{test_product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Product"
    assert data["specification"] == "This is a test product."
    assert data["price_today"] is None
    assert data["lowest_price"] is None
    assert data["mean"] is None

def test_read_product_with_prices(test_user, test_price_history):
    product = test_price_history([1000,900,800])
    response = client.get(f"/products/{product.id}")
    data = response.json()
    assert data["lowest_price"] == "R$ 8,00"
    assert data["price_today"] == "R$ 10,00"
    assert data["mean"] == "R$ 9,00"
    assert response.status_code == 200

def test_read_product_with_nulls(test_user, test_price_history):
    product = test_price_history([1000,None,800])
    response = client.get(f"/products/{product.id}")
    data = response.json()
    assert data["lowest_price"] == "R$ 8,00"
    assert data["price_today"] == "R$ 10,00"
    assert data["mean"] == "R$ 9,00"
    assert response.status_code == 200

def test_read_product_not_found(test_user):
    response = client.get("/products/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Product Not Found"

def test_unfollow_product(test_user, test_product):
    response = client.delete(f"/products/{test_product.id}")
    assert response.status_code == 204

    response = client.delete(f"/products/{test_product.id}")
    assert response.status_code == 404

