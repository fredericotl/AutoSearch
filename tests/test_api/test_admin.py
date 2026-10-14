from app.core import get_admin
from app.db import get_db
from tests.test_api.utils import *

app.dependency_overrides[get_db] = override_get_db

app.dependency_overrides[get_admin] = override_get_admin

def test_create_invite_success():
    response = client.post("/admin/invites", json={
        "email": "newuser@gmail.com",
        "invited_role": "default"
    })
    assert response.status_code == 201
    data = response.json()
    assert len(data["token"]) == 16
    db = TestingSessionLocal()
    invite = db.query(Invite).first()
    assert invite.email == "newuser@gmail.com"
    assert invite.token_hash == hash_invite_token(data["token"])
    assert invite.used is False


def test_admin_delete_product(test_product):
    response = client.delete(f"/admin/{test_product.id}")
    assert response.status_code == 204

    db = TestingSessionLocal()
    assert db.get(Product, test_product.id) is None

def test_admin_delete_product_not_found():
    response = client.delete("/admin/999")
    assert response.status_code == 404