def _create(client, **overrides):
    payload = {"name": "Widget", "price": 9.99, **overrides}
    return client.post("/items", json=payload)


def test_list_items_starts_empty(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item(client):
    response = _create(client, name="Gadget", price=19.5)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Gadget"
    assert body["price"] == 19.5


def test_get_item(client):
    item_id = _create(client).json()["id"]
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_get_missing_item_returns_404(client):
    response = client.get("/items/999")
    assert response.status_code == 404


def test_partial_update_item(client):
    item_id = _create(client, price=10.0).json()["id"]
    response = client.patch(f"/items/{item_id}", json={"price": 12.0})
    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 12.0
    assert body["name"] == "Widget"  # unchanged


def test_delete_item(client):
    item_id = _create(client).json()["id"]
    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404


def test_create_item_rejects_negative_price(client):
    response = _create(client, price=-1)
    assert response.status_code == 422
