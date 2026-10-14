from app.core import get_current_user
from app.db import get_db
from tests.test_api.utils import *
from app.core import get_current_user, WINDOW_OF_DAYS


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

def test_read_all_products_user_not_found():
    response = client.get("/products/")
    assert response.status_code == 401
    assert response.json()["detail"] == "User Not Found"

def test_read_product_not_found(test_user):
    response = client.get("/products/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Product Not Found"

def test_read_product_two_prices_same_day(test_user, test_price_history):
    test_price_history([1000,900,800])
    product = test_price_history([700])
    response = client.get(f"/products/{product.id}")
    data = response.json()
    assert data["lowest_price"] == "R$ 7,00"
    assert data["price_today"] == "R$ 7,00"
    assert data["mean"] == "R$ 8,00"
    assert response.status_code == 200

def test_unfollow_product(test_user, test_product):
    response = client.post(f"/products/{test_product.id}/unfollow")
    assert response.status_code == 204

    db = TestingSessionLocal()
    product = db.get(Product, test_product.id)
    assert product is not None
    assert product.is_search_active is False
    assert product.viewers == []

    response = client.post(f"/products/{test_product.id}/unfollow")
    assert response.status_code == 400

def test_lowest_price_never_above_today(test_user, test_price_history):
    product = test_price_history([700, 900, 800])
    response = client.get(f"/products/{product.id}")
    data = response.json()
    assert response.status_code == 200
    assert data["price_today"] == "R$ 7,00"
    assert data["lowest_price"] == data["price_today"]

def test_same_prices_in_both_routes(test_user, test_price_history):
    product = test_price_history([1000, 900, 800])
    one = client.get(f"/products/{product.id}").json()
    listed = client.get("/products/").json()["products"]
    assert one["lowest_price"] is not None
    assert len(listed) == 1
    assert listed[0] == one

def test_price_outside_window_ignored(test_user, test_price_history):
    test_price_history([1000, 900])
    product = test_price_history([100], days_ago=WINDOW_OF_DAYS + 1)
    data = client.get(f"/products/{product.id}").json()
    assert data["lowest_price"] == "R$ 9,00"
    assert data["mean"] == "R$ 9,50"