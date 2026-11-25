"""Pruebas de los endpoints de productores: crear, documento duplicado y listar."""

import pytest

def test_create_producer(client, producer_payload):
    response = client.post("/producers", json=producer_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["document_number"] == "1234567890"
    assert body["full_name"] == "Ana Pérez"
    assert body["municipality"] == "Tumaco"
    assert body["created_at"]  # lo asigna la base de datos
    assert body["farm"] is None  # aún no tiene finca

def test_create_producer_with_duplicate_document_returns_409(client, producer_payload):
    assert client.post("/producers", json=producer_payload).status_code == 201

    other = {**producer_payload, "full_name": "Otra Persona", "municipality": "Cali"}
    response = client.post("/producers", json=other)

    assert response.status_code == 409
    assert "documento" in response.json()["detail"]
    assert len(client.get("/producers").json()) == 1  # no se creó el segundo

@pytest.mark.parametrize(
    "change",
    [
        {"document_number": None},  # campo faltante (se elimina)
        {"full_name": "   "},  # solo espacios
        {"document_number": "9" * 33},  # más largo que la columna
        {"id": 99},  # campos que el cliente no puede enviar
        {"created_at": "2020-01-01T00:00:00"},
    ],
    ids=["campo_faltante", "solo_espacios", "documento_largo", "id_extra", "created_at_extra"],
)
def test_create_producer_with_invalid_payload_returns_422(client, producer_payload, change):
    payload = {**producer_payload, **change}
    payload = {key: value for key, value in payload.items() if value is not None}

    assert client.post("/producers", json=payload).status_code == 422

def test_list_producers(client, producer_payload):
    assert client.get("/producers").json() == []

    client.post("/producers", json=producer_payload)
    client.post("/producers", json={**producer_payload, "document_number": "2"})
    listed = client.get("/producers").json()

    assert [p["document_number"] for p in listed] == ["1234567890", "2"]