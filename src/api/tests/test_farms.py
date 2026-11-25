"""Pruebas de la finca: subir un GeoJSON válido o inválido y consultarlo como Feature."""

import json

import pytest
from pyproj import Geod
from shapely.geometry import Polygon

def feature(geometry):
    return {"type": "Feature", "properties": {}, "geometry": geometry}

# Cuadrado de ~100 ha cerca de Tumaco, como [longitud, latitud] y con el anillo cerrado.
SQUARE = [[-78.80, 1.80], [-78.80, 1.809], [-78.791, 1.809], [-78.791, 1.80], [-78.80, 1.80]]
POLYGON = {"type": "Polygon", "coordinates": [SQUARE]}
FEATURE = {"type": "Feature", "properties": {"name": "El Cacaotal"}, "geometry": POLYGON}
INVALID_GEOJSON = {
    "json_malformado": (b"{esto no es json", "JSON válido"),
    "punto": ({"type": "Point", "coordinates": [-78.8, 1.8]}, "Polygon"),
    "multipolygon": ({"type": "MultiPolygon", "coordinates": [[SQUARE]]}, "Polygon"),
    "dos_poligonos": (
        {"type": "FeatureCollection", "features": [feature(POLYGON), feature(POLYGON)]},
        "exactamente un polígono",
    ),
    "sin_cerrar": (
        {"type": "Polygon", "coordinates": [SQUARE[:-1] + [[-78.7905, 1.8005]]]},
        "no está cerrado",
    ),
    "auto_interseccion": (  # lazo: los lados se cruzan
        {"type": "Polygon", "coordinates": [[[-78.80, 1.80], [-78.79, 1.81], [-78.79, 1.80], [-78.80, 1.81], [-78.80, 1.80]]]},
        "no es válido",
    ),
    "fuera_de_colombia": (  # Madrid
        {"type": "Polygon", "coordinates": [[[-3.70, 40.41], [-3.70, 40.42], [-3.69, 40.42], [-3.69, 40.41], [-3.70, 40.41]]]},
        "dentro de Colombia",
    ),
    "latitud_longitud_invertidas": (
        {"type": "Polygon", "coordinates": [[[lat, lon] for lon, lat in SQUARE]]},
        "invertidas",
    ),
}

def upload(client, producer_id, payload, **form):
    """Sube `payload` (dict o bytes) como archivo .geojson al endpoint de finca."""

    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    files = {"file": ("finca.geojson", raw, "application/geo+json")}
    return client.post(f"/producers/{producer_id}/farm", files=files, data=form)

def geodesic_ha(ring) -> float:
    """Área de referencia calculada de forma independiente (geodésica, en hectáreas)."""

    return abs(Geod(ellps="WGS84").geometry_area_perimeter(Polygon(ring))[0]) / 10_000

def test_upload_valid_geojson(client, producer):
    response = upload(client, producer["id"], POLYGON)

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "Feature"
    assert body["geometry"] == POLYGON
    assert body["properties"]["name"] == "Finca de Ana Pérez"
    # El área la calcula el servidor y coincide con el cálculo geodésico.
    assert body["properties"]["area_ha"] == pytest.approx(geodesic_ha(SQUARE), rel=1e-3)

def test_get_farm_returns_feature_with_name_and_area(client, producer):
    upload(client, producer["id"], POLYGON, name="La Esperanza")

    response = client.get(f"/producers/{producer['id']}/farm")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] == "Polygon"
    assert body["properties"]["name"] == "La Esperanza"
    assert body["properties"]["area_ha"] > 0
    # El listado de productores trae un resumen de la finca, sin geometría.
    assert client.get("/producers").json()[0]["farm"]["name"] == "La Esperanza"

@pytest.mark.parametrize(
    "payload",
    [
        FEATURE,
        {"type": "FeatureCollection", "features": [FEATURE]},
        {"type": "Polygon", "coordinates": [[[x, y, 1500] for x, y in SQUARE]]},  # con altitud
    ],
    ids=["feature", "feature_collection", "con_altitud"],
)
def test_upload_accepts_other_valid_formats(client, producer, payload):
    response = upload(client, producer["id"], payload)

    assert response.status_code == 201
    assert response.json()["geometry"] == POLYGON  # se normaliza a Polygon en 2D

def test_farm_name_comes_from_form_then_feature_then_default(client, producer_payload):
    names = []
    for index, (payload, form) in enumerate(
        [(FEATURE, {"name": "Del formulario"}), (FEATURE, {}), (POLYGON, {})], start=1
    ):
        created = client.post("/producers", json={**producer_payload, "document_number": str(index)})
        response = upload(client, created.json()["id"], payload, **form)
        names.append(response.json()["properties"]["name"])

    assert names == ["Del formulario", "El Cacaotal", "Finca de Ana Pérez"]

@pytest.mark.parametrize(
    "payload, message",
    list(INVALID_GEOJSON.values()),
    ids=list(INVALID_GEOJSON),
)
def test_upload_invalid_geojson_returns_422_with_clear_message(client, producer, payload, message):
    response = upload(client, producer["id"], payload)

    assert response.status_code == 422
    assert message in response.json()["detail"]
    # Un archivo inválido no deja ninguna finca guardada.
    assert client.get(f"/producers/{producer['id']}/farm").status_code == 404

def test_producer_can_only_have_one_farm(client, producer):
    assert upload(client, producer["id"], POLYGON).status_code == 201

    assert upload(client, producer["id"], POLYGON).status_code == 409

def test_farm_endpoints_return_404_when_missing(client, producer):
    assert upload(client, 999, POLYGON).status_code == 404  # productor inexistente
    assert client.get("/producers/999/farm").status_code == 404
    assert client.get(f"/producers/{producer['id']}/farm").status_code == 404  # sin finca