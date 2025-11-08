import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from order_service.orders.models import Order, OrderItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixturex
def sample_order(db):
    return Order.objects.create(user_id=10)


@pytest.fixture
def sample_item(db, sample_order):
    return OrderItem.objects.create(
        order=sample_order,
        product_variation=1,
        quantity=2,
        price=10,
        status=1
    )


# 1️⃣ GET + POST /orders/
@pytest.mark.django_db
def test_orders_list_get(api_client, sample_order):
    url = reverse("orders_list_create")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_orders_create(api_client):
    url = reverse("orders_list_create")
    data = {"user_id": 11}
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["user_id"] == 11


# 2️⃣ GET / PATCH / DELETE /orders/<id>/
@pytest.mark.django_db
def test_order_detail_get(api_client, sample_order):
    url = reverse("orders_detail", args=[sample_order.id])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == sample_order.id


@pytest.mark.django_db
def test_order_detail_patch(api_client, sample_order):
    url = reverse("orders_detail", args=[sample_order.id])
    data = {"user_id": 22}
    response = api_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user_id"] == 22


@pytest.mark.django_db
def test_order_detail_delete(api_client, sample_order):
    url = reverse("orders_detail", args=[sample_order.id])
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


# 3️⃣ GET + POST /order-items/
@pytest.mark.django_db
def test_orderitems_list_get(api_client, sample_item):
    url = reverse("orderitems_list_create")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_orderitems_create(api_client, sample_order):
    url = reverse("orderitems_list_create")
    data = {
        "order": sample_order.id,
        "product_variation": 5,
        "quantity": 3,
        "price": 25
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["order"] == sample_order.id


# 4️⃣ GET / PATCH / DELETE /order-items/<id>/
@pytest.mark.django_db
def test_orderitems_detail_get(api_client, sample_item):
    url = reverse("orderitems_detail", args=[sample_item.id])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_orderitems_detail_patch(api_client, sample_item):
    url = reverse("orderitems_detail", args=[sample_item.id])
    data = {"quantity": 10}
    response = api_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["quantity"] == 10


@pytest.mark.django_db
def test_orderitems_detail_delete(api_client, sample_item):
    url = reverse("orderitems_detail", args=[sample_item.id])
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


# 5️⃣ POST /create-order-from-shopcart/
@pytest.mark.django_db
def test_create_order_from_shopcart(api_client):
    url = reverse("create_order_from_shopcart")
    data = {
        "user_id": 33,
        "items": [
            {"product_variation": 1, "quantity": 2, "price": 50},
            {"product_variation": 2, "quantity": 1, "price": 20},
        ],
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Order created successfully"


# 6️⃣ PATCH /update-order-item-status/<id>/
@pytest.mark.django_db
def test_update_order_item_status(api_client, sample_item, monkeypatch):
    # mock send_order_completed_event
    monkeypatch.setattr("order_service.tasks.send_order_completed_event", lambda x: None)
    
    url = reverse("update_order_item_status", args=[sample_item.id])
    data = {"status": 3}
    response = api_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == 3