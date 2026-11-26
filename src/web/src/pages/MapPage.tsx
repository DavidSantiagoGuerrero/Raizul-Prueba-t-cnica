
import { useEffect, useState } from "react";

import {
  MapContainer,
  Marker,
  TileLayer,
  Popup,
  Polygon,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";

import {
  divIcon,
  type LatLngExpression,
} from "leaflet";

import "leaflet/dist/leaflet.css";
import "../styles/Map.css";

import {
  ApiError,
  getFarm,
  listProducers,
  type FarmFeature,
  type Producer,
} from "../services/api";

// Información de cada productor y su finca.
interface FarmEntry {
  producer: Producer;
  farm: FarmFeature;
}

interface HoveredFarm {
  producerName: string;
  position: LatLngExpression;
}

interface SelectedFarm {
  producerName: string;
  farmName: string;
  municipality: string;
  area: number;
  position: LatLngExpression;
}

// Zoom a partir del cual se muestran los polígonos.
const POLYGON_ZOOM = 13;

// Límites aproximados de Colombia.
// Leaflet utiliza [latitud, longitud].
const MAX_BOUNDS: [[number, number], [number, number]] = [
  [-6, -82],
  [14, -63],
];

// Calcula el centro aproximado de un polígono.
function getPolygonCenter(farm: FarmFeature): [number, number] {
  const ring = farm.geometry.coordinates[0] ?? [];

  // Elimina el último punto, que normalmente repite el primero.
  const points = ring.length > 1
    ? ring.slice(0, -1)
    : ring;

  if (points.length === 0) {
    return [0, 0];
  }

  let longitude = 0;
  let latitude = 0;

  points.forEach(([lng, lat]) => {
    longitude += lng;
    latitude += lat;
  });

  return [
    latitude / points.length,
    longitude / points.length,
  ];
}

// Convierte las coordenadas GeoJSON [longitud, latitud]
// al formato de Leaflet [latitud, longitud].
function getPolygonPositions(
  farm: FarmFeature,
): LatLngExpression[][] {
  return farm.geometry.coordinates.map((ring) =>
    ring.map(([lng, lat]) => [lat, lng] as LatLngExpression),
  );
}

// Construye un pin personalizado.
function createPinIcon(scale: number) {
  return divIcon({
    className: "farm-pin-wrapper",
    html: `
      <span
        class="farm-pin"
        style="--pin-scale: ${scale}"
      ></span>
    `,
    iconSize: [40, 44],
    iconAnchor: [20, 44],
  });
}

// Componente que detecta el zoom y mantiene el mapa
// actualizado cuando cambia el tamaño de su contenedor.
function MapBehavior({
  onZoomChange,
}: {
  onZoomChange: (zoom: number) => void;
}) {
  const map = useMap();

  useMapEvents({
    zoomend: () => {
      onZoomChange(map.getZoom());
    },
  });

  useEffect(() => {
    const container = map.getContainer();

    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });

    observer.observe(container);
    map.invalidateSize();

    return () => {
      observer.disconnect();
    };
  }, [map]);

  return null;
}

// Componente que dibuja las fincas y sus marcadores.
function FarmLayers({
  entries,
  zoom,
}: {
  entries: FarmEntry[];
  zoom: number;
}) {
  const map = useMap();

  const [hoveredFarm, setHoveredFarm] =
    useState<HoveredFarm | null>(null);

  const [selectedFarm, setSelectedFarm] =
    useState<SelectedFarm | null>(null);

  // El pin comienza grande y se reduce progresivamente.
  const pinScale = Math.max(
    0.45,
    1.2 - Math.max(0, zoom - 5) * 0.1,
  );

  const showPolygons = zoom >= POLYGON_ZOOM;

  // Limpiamos los cuadros al cambiar entre pines y polígonos.
  useEffect(() => {
    setHoveredFarm(null);
    setSelectedFarm(null);
  }, [showPolygons]);

  return (
    <>
      {entries.map(({ producer, farm }) => {
        const center = getPolygonCenter(farm);

        const farmName =
          farm.properties.name || "Finca sin nombre";

        const area = Number(farm.properties.area_ha);

        // Vista alejada: mostrar pines.
        if (!showPolygons) {
          return (
            <Marker
              key={`marker-${producer.id}`}
              position={center}
              icon={createPinIcon(pinScale)}
              eventHandlers={{
                click: () => {
                  map.flyTo(
                    center,
                    15.5,
                    { duration: 1 },
                  );
                },
              }}
            >
              <Popup>
                <div className="farm-popup">
                  <p>
                    <strong>Productor:</strong>{" "}
                    {producer.full_name}
                  </p>

                  <p>
                    <strong>Finca:</strong>{" "}
                    {farmName}
                  </p>

                  <p>
                    <strong>Municipio:</strong>{" "}
                    {producer.municipality}
                  </p>

                  <p>
                    <strong>Área:</strong>{" "}
                    {area.toLocaleString("es-CO")} ha
                  </p>
                </div>
              </Popup>
            </Marker>
          );
        }

        // Vista cercana: mostrar polígonos.
        const positions = getPolygonPositions(farm);

        return (
          <Polygon
            key={`polygon-${producer.id}`}
            positions={positions}
            pathOptions={{
              color: "#155c2e",
              weight: 2,
              fillColor: "#258746",
              fillOpacity: 1,
            }}
            eventHandlers={{
              // Mostrar nombre del productor al pasar el mouse.
              mouseover: (event) => {
                setHoveredFarm({
                  producerName: producer.full_name,
                  position: event.latlng,
                });
              },

              mouseout: () => {
                setHoveredFarm(null);
              },

              // Mostrar información completa al hacer clic.
              click: (event) => {
                setSelectedFarm({
                  producerName: producer.full_name,
                  farmName,
                  municipality: producer.municipality,
                  area,
                  position: event.latlng,
                });
              },
            }}
          >
            {/* Nombre permanente en el centro de la finca. */}
            <Tooltip
              permanent
              direction="center"
              opacity={1}
              className="farm-name-tooltip"
            >
              {farmName}
            </Tooltip>
          </Polygon>
        );
      })}

      {/* Información del productor al pasar el cursor. */}
      {hoveredFarm && showPolygons && (
        <Tooltip
          position={hoveredFarm.position}
          permanent
          direction="top"
          opacity={1}
          className="farm-producer-tooltip"
        >
          <strong>Productor:</strong>{" "}
          {hoveredFarm.producerName}
        </Tooltip>
      )}

      {/* Información completa al hacer clic en una finca. */}
      {selectedFarm && showPolygons && (
        <Popup
          position={selectedFarm.position}
          eventHandlers={{
            remove: () => setSelectedFarm(null),
          }}
        >
          <div className="farm-popup">
            <p>
              <strong>Productor:</strong>{" "}
              {selectedFarm.producerName}
            </p>

            <p>
              <strong>Finca:</strong>{" "}
              {selectedFarm.farmName}
            </p>

            <p>
              <strong>Municipio:</strong>{" "}
              {selectedFarm.municipality}
            </p>

            <p>
              <strong>Área:</strong>{" "}
              {selectedFarm.area.toLocaleString("es-CO")} ha
            </p>
          </div>
        </Popup>
      )}
    </>
  );
}

export default function MapPage() {
  const [entries, setEntries] = useState<FarmEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(5);

  // 1. Consultar productores y sus fincas.
  useEffect(() => {
    let cancelled = false;

    async function loadFarms() {
      try {
        const producers = await listProducers();

        const results = await Promise.all(
          producers.map(async (producer) => {
            try {
              const farm = await getFarm(producer.id);

              return {
                producer,
                farm,
              };
            } catch (err) {
              // Un productor sin finca no representa un error.
              if (
                err instanceof ApiError &&
                err.status === 404
              ) {
                return null;
              }

              throw err;
            }
          }),
        );

        if (cancelled) return;

        setEntries(
          results.filter(
            (result): result is FarmEntry => result !== null,
          ),
        );
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "No se pudieron cargar las fincas.",
          );
        }
      }
    }

    loadFarms();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="map-wrap">
      <MapContainer
        center={[4.5, -73.5]}
        zoom={5}
        minZoom={4}
        maxZoom={19}
        maxBounds={MAX_BOUNDS}
        maxBoundsViscosity={1}
        scrollWheelZoom
        className="map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        <MapBehavior onZoomChange={setZoom} />

        {entries && (
          <FarmLayers
            entries={entries}
            zoom={zoom}
          />
        )}
      </MapContainer>

      {/* Estado de carga. */}
      {entries === null && !error && (
        <div className="map-overlay">
          Cargando fincas...
        </div>
      )}

      {/* Errores de la API. */}
      {error && (
        <div className="map-overlay map-overlay-error">
          {error}
        </div>
      )}

      {/* Leyenda inferior. */}
      {entries !== null && (
        <div className="map-legend">
          {entries.length === 0
            ? "Aún no hay fincas registradas."
            : `${entries.length} ${entries.length === 1 ? "finca" : "fincas"
            } registradas · Acércate para ver sus delimitaciones.`}
        </div>
      )}
    </div>
  );
}
