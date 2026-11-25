"""Validación del GeoJSON de una finca y cálculo de su área.

`parse_farm_geojson` recibe los bytes del archivo subido y devuelve la geometría
normalizada (un `Polygon` en 2D), el área en hectáreas y un nombre sugerido (si
el GeoJSON es un Feature con `properties.name`). Si algo falla lanza
`GeoJSONError` con un mensaje claro, que el router convierte en HTTP 422.

Área: se reproyecta de WGS84 (EPSG:4326) a EPSG:6933 (WGS 84 / NSIDC EASE-Grid 2.0
Global, una proyección métrica de áreas iguales) con pyproj y se calcula con Shapely.
Al conservar las áreas, el resultado coincide con el cálculo geodésico en todo el país.
"""

import json
import math
from dataclasses import dataclass
from typing import Any

from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform
from shapely.validation import explain_validity

# Límites aproximados de Colombia (grados, WGS84).
LON_MIN, LON_MAX = -79.0, -66.0
LAT_MIN, LAT_MAX = -4.3, 12.5
AREA_CRS = "EPSG:6933"  # equal-area: preserva las áreas
M2_PER_HA = 10_000

class GeoJSONError(ValueError):
    """GeoJSON inválido."""

@dataclass
class ParsedFarm:
    """Resultado de validar el archivo."""

    geometry: dict[str, Any]  # {"type": "Polygon", "coordinates": [...]} en 2D
    area_ha: float
    name: str | None  # `properties.name` del Feature, si existía

def name_from(properties: Any) -> str | None:
    """Toma `properties.name` si es un texto no vacío (recortado a 200 caracteres)."""

    if isinstance(properties, dict):
        value = properties.get("name")
        if isinstance(value, str) and value.strip():
            return value.strip()[:200]
    return None

def extract_polygon(data: Any) -> tuple[dict[str, Any], str | None]:
    """Obtiene el único Polygon de un Polygon, Feature o FeatureCollection."""

    if not isinstance(data, dict):
        raise GeoJSONError("El GeoJSON debe ser un objeto JSON.")

    kind = data.get("type")
    name = None

    if kind == "FeatureCollection":
        features = data.get("features")

        if not isinstance(features, list) or len(features) != 1:
            found = len(features) if isinstance(features, list) else 0
            raise GeoJSONError(
                f"El FeatureCollection debe contener exactamente un polígono (tiene {found})."
            )

        data = features[0]

        if not isinstance(data, dict):
            raise GeoJSONError("El Feature del FeatureCollection no es válido.")

        kind = data.get("type")
    
    if kind == "Feature":
        name = name_from(data.get("properties"))
        geometry = data.get("geometry")
    elif kind == "Polygon":
        geometry = data
    else:
        raise GeoJSONError(
            f"El tipo debe ser Polygon, Feature o FeatureCollection (recibido: {kind!r})."
        )

    geometry_type = geometry.get("type") if isinstance(geometry, dict) else None

    if geometry_type != "Polygon":
        raise GeoJSONError(
            f"La geometría debe ser un Polygon (recibido: {geometry_type!r}). "
            "No se admiten MultiPolygon ni otros tipos."
        )

    return geometry, name

def is_position(position: Any) -> bool:
    """True si es una lista de al menos dos números finitos (no booleanos)."""

    return (
        isinstance(position, list)
        and len(position) >= 2
        and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            for v in position[:2]
        )
    )

def clean_rings(coordinates: Any) -> list[list[list[float]]]:
    """Comprueba la estructura de los anillos y los normaliza a [lon, lat]."""

    if not isinstance(coordinates, list) or not coordinates:
        raise GeoJSONError("El polígono no tiene coordenadas.")

    rings = []
    for number, ring in enumerate(coordinates, start=1):
        if not isinstance(ring, list) or len(ring) < 4:
            raise GeoJSONError(
                f"El anillo {number} necesita al menos 4 posiciones "
                "(la última igual a la primera)."
            )
        clean = []
        for position in ring:
            if not is_position(position):
                raise GeoJSONError(
                    "Cada posición debe ser [longitud, latitud] con números finitos."
                )
            clean.append([float(position[0]), float(position[1])])  # descarta la altitud
        rings.append(clean)
    return rings

def check_closed(rings: list[list[list[float]]]) -> None:
    """Cada anillo debe terminar en la misma coordenada con la que empieza."""

    for number, ring in enumerate(rings, start=1):
        if ring[0] != ring[-1]:
            raise GeoJSONError(
                f"El polígono no está cerrado: en el anillo {number} la primera y la "
                "última coordenada deben ser iguales."
            )

def in_colombia(lon: float, lat: float) -> bool:
    return LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX

def check_colombia(rings: list[list[list[float]]]) -> None:
    """Todas las coordenadas deben caer dentro de los límites de Colombia."""

    points = [p for ring in rings for p in ring]
    outside = next((p for p in points if not in_colombia(p[0], p[1])), None)
    if outside is None:
        return

    message = (
        f"Las coordenadas deben estar dentro de Colombia (longitud entre {LON_MIN} y "
        f"{LON_MAX}, latitud entre {LAT_MIN} y {LAT_MAX}). "
        f"Primera coordenada fuera de rango: {outside}."
    )
    if all(in_colombia(p[1], p[0]) for p in points):
        message += " Parece que latitud y longitud están invertidas: GeoJSON usa [longitud, latitud]."
    raise GeoJSONError(message)

def area_m2(polygon: Polygon) -> float:
    """Área en m² tras reproyectar a una proyección métrica."""

    # El Transformer se crea por llamada para no compartir estado entre hilos.
    transformer = Transformer.from_crs("EPSG:4326", AREA_CRS, always_xy=True)
    return transform(transformer.transform, polygon).area

def parse_farm_geojson(raw: bytes) -> ParsedFarm:
    """Valida el archivo y devuelve la geometría normalizada y su área."""

    try:
        data = json.loads(raw)
    except (ValueError, RecursionError):  # JSON mal formado o UTF-8 inválido
        raise GeoJSONError("El archivo no es un JSON válido.") from None

    geometry, name = extract_polygon(data)
    rings = clean_rings(geometry.get("coordinates"))
    check_closed(rings)
    check_colombia(rings)

    polygon = Polygon(rings[0], rings[1:])

    if not polygon.is_valid:
        raise GeoJSONError(
            f"El polígono no es válido: {explain_validity(polygon)}. "
            "Revisa que no tenga auto-intersecciones."
        )

    area_ha = round(area_m2(polygon) / M2_PER_HA, 4)
    
    if area_ha <= 0:
        raise GeoJSONError("El polígono es demasiado pequeño: su área es prácticamente cero.")

    return ParsedFarm({"type": "Polygon", "coordinates": rings}, area_ha, name)
