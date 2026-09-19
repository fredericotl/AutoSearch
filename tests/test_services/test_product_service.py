from app.services.product_service import (get_watched_products, get_all_products, get_product,create_product,
                                          remove_product, _get_product_response)
from app.services.price_service import ProductPrices
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from app.models import Product, User
from app.schemas import CreateProduct
from app.core import ProductNotFound, UserNotFollow
import pytest

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def mock_product():
    mock_product = MagicMock(spec=Product)
    mock_product.id = 1
    mock_product.title = "Test Product"
    mock_product.link = "http://example.com/product/1"
    mock_product.specification = "Test Specification"
    mock_product.owner_id = 1
    mock_product.is_search_active = True
    return mock_product

def mock_user(user_id:int = 1):
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.email = f"example{user_id}@example.com"
    mock_user.username = f"user{user_id}"
    mock_user.first_name = f"First{user_id}"
    mock_user.last_name = f"Last{user_id}"
    mock_user.hashed_password = "hashed_password"
    mock_user.is_active = True
    mock_user.watching = []
    return mock_user

def test_get_watched_products():
    db = mock_db_session()
    user = mock_user()
    product1 = mock_product()
    product2 = mock_product()
    user.watching = [product1, product2]
    db.get.return_value = user
    result = get_watched_products(db, 1)
    assert result == [product1, product2]

def test_get_all_products():
    db = mock_db_session()
    product1 = mock_product()
    product2 = mock_product()
    db.query.return_value.options.return_value.where.return_value.all.return_value = [product1, product2]
    result = get_all_products(db)
    assert result == [product1, product2]

def test_get_product_success():
    db = mock_db_session()
    product = mock_product()
    product.title = "Test Product"
    db.get.return_value = product
    result = get_product(db, 1)
    db.get.assert_called_once_with(Product, 1)
    assert result == product
    assert result.title == "Test Product"

def test_get_product_not_found():
    db = mock_db_session()
    db.get.return_value = None
    with pytest.raises(ProductNotFound) as exinfo:
        get_product(db, 1)
    assert str(exinfo.value) == "Product Not Found"

def test_get_product_response():
    prices = {1: ProductPrices(history=[100, 300, 200], price_today=150)}
    product =mock_product()
    response = _get_product_response(prices=prices, product=product)
    assert response.id == product.id
    assert response.title == product.title
    assert response.link == product.link
    assert response.specification == product.specification
    assert response.price_today == "R$ 1,50"
    assert response.lowest_price == "R$ 1,00"
    assert response.mean == "R$ 2,00"

def test_get_product_response_none():
    prices = {1: ProductPrices(history=[], price_today=None)}
    product =mock_product()
    response = _get_product_response(prices=prices, product=product)
    assert response.id == product.id
    assert response.price_today is None
    assert response.lowest_price is None
    assert response.mean is None

def test_create_product_success():
    db = mock_db_session()
    product_request = CreateProduct(
        title="New Product",
        link="http://example.com/product/new",
        specification="New Specification"
    )
    owner = mock_user(1)
    db.get.return_value = owner

    with patch('app.services.product_service.Product') as MockProduct:
        mock_product_instance = MagicMock(spec=Product)
        mock_product_instance.title = "New Product"
        mock_product_instance.link = "http://example.com/product/new"
        mock_product_instance.specification = "New Specification"
        mock_product_instance.owner_id = 1
        mock_product_instance.viewers = [owner]

        MockProduct.return_value = mock_product_instance

        result = create_product(db, product_request, 1)

        MockProduct.assert_called_once()
        assert result.title == "New Product"
        assert result.owner_id == 1
        assert db.add.called


def test_remove_product_user_not_follower():
    db = mock_db_session()
    product = mock_product()
    user = mock_user(1)
    other_user = mock_user(2)

    product.viewers = [other_user]
    db.get.return_value = user

    with pytest.raises(UserNotFollow):
        remove_product(db, product, 1)


def test_remove_product_last_viewer_deletes():
    db = mock_db_session()
    product = mock_product()
    user = mock_user(1)

    product.viewers = [user]
    product.id = 1
    db.get.return_value = user

    with patch('app.services.product_service.remove_detections') as mock_remove_det:
        remove_product(db, product, 1)
        mock_remove_det.assert_called_once_with(db, 1)
        db.delete.assert_called_once_with(product)


def test_remove_product_multiple_viewers_removes_user():
    db = mock_db_session()
    product = mock_product()
    user1 = mock_user(1)
    user2 = mock_user(2)

    product.viewers = [user1, user2]
    product.owner_id = 1
    db.get.return_value = user1

    remove_product(db, product, 1)

    assert user1 not in product.viewers
    db.delete.assert_not_called()


def test_remove_product_user_is_owner():
    db = mock_db_session()
    product = mock_product()
    user1 = mock_user(1)
    user2 = mock_user(2)


    product.viewers = [user1, user2]
    product.owner_id = 1
    db.get.return_value = user1

    remove_product(db, product, 1)

    assert product.owner_id is None
    assert user1 not in product.viewers
    db.delete.assert_not_called()