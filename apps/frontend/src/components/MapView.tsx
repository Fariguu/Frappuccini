import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMapEvents, Polyline } from 'react-leaflet';
import L from 'leaflet';
import type { EventScenario } from '../types/scenario';

// Fix for default marker icons
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

interface MapViewProps {
    scenario: EventScenario;
    onMapClick?: (latlng: [number, number]) => void;
}

// Center of Bari
const BARI_CENTER: [number, number] = [41.1171, 16.8719];

// Mock GeoJSON for roads
const MOCK_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        { "type": "Feature", "properties": { "id": "road1", "name": "Via Sparano", "threshold": 0 }, "geometry": { "type": "LineString", "coordinates": [[16.8700, 41.1200], [16.8700, 41.1100]] } },
        { "type": "Feature", "properties": { "id": "road2", "name": "Corso Vittorio Emanuele", "threshold": 2000 }, "geometry": { "type": "LineString", "coordinates": [[16.8600, 41.1250], [16.8850, 41.1250]] } },
        { "type": "Feature", "properties": { "id": "road3", "name": "Lungomare", "threshold": 5000 }, "geometry": { "type": "LineString", "coordinates": [[16.8750, 41.1300], [16.9000, 41.1200]] } }
    ]
};

// Mock AMTAB & Sharing Nodes
const AMTAB_STOPS: [number, number][] = [[41.121, 16.865], [41.122, 16.875], [41.123, 16.885]];
const SHARING_NODES: [number, number][] = [[41.115, 16.868], [41.118, 16.872], [41.112, 16.878]];

const MapEvents = ({ onClick }: { onClick: (latlng: [number, number]) => void }) => {
    useMapEvents({
        click: (e) => onClick([e.latlng.lat, e.latlng.lng]),
    });
    return null;
};

const Legend: React.FC = () => {
    return (
        <div className="absolute bottom-4 left-4 bg-white/90 border border-secondary/20 p-2 text-[9px] uppercase font-bold tracking-tighter z-[1000] shadow-md flex flex-col gap-1">
            <div className="flex items-center gap-2">
                <div className="w-4 h-[1px] bg-[#878787]"></div> <span>Rete stradale base</span>
            </div>
            <div className="flex items-center gap-2">
                <div className="w-4 h-[2px] bg-[#000000]"></div> <span>Traffico previsto</span>
            </div>
        </div>
    );
};

const MapView: React.FC<MapViewProps> = ({ scenario, onMapClick }) => {
    const [geoData, setGeoData] = useState<any>(null);
    const [isSimulation, setIsSimulation] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/map');
                if (!response.ok) throw new Error();
                const data = await response.json();
                if (data.error) throw new Error();
                setGeoData(data);
                setIsSimulation(false);
            } catch {
                setGeoData(MOCK_GEOJSON);
                setIsSimulation(true);
            }
        };
        fetchData();
    }, []);

    const roadStyle = (feature: any) => {
        const props = feature?.properties || {};
        const threshold = props.threshold ?? 0;
        const participants = scenario.event.totalPeople;
        const isActive = participants >= threshold;
        const virtualIntensity = Math.min(100, participants / 100);
        return {
            color: isActive ? "#000000" : "#878787",
            weight: isActive ? (2 + virtualIntensity / 20) : 1,
            opacity: isActive ? 1 : 0.4,
        };
    };

    return (
        <div className="flex-1 bg-background relative overflow-hidden flex items-center justify-center">
            {isSimulation && (
                <div className="absolute top-4 left-4 bg-zinc-900 text-white px-3 py-1 text-[10px] font-bold z-[2000] uppercase tracking-widest shadow-lg flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
                    FALLBACK: dati mock (backend non disponibile)
                </div>
            )}

            <div className="absolute top-4 right-4 bg-white/80 border border-secondary/20 p-2 text-[10px] font-mono uppercase tracking-widest z-[1000] shadow-sm">
                GIS View: Cartografia_Bari_v02
            </div>

            <MapContainer center={BARI_CENTER} zoom={14} className="w-full h-full" zoomControl={false}>
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; OSM'
                />

                {onMapClick && <MapEvents onClick={onMapClick} />}

                {geoData && (
                    <GeoJSON
                        key={`${isSimulation}-${scenario.event.totalPeople}`}
                        data={geoData}
                        style={roadStyle}
                    />
                )}

                {/* Dynamic Route Polyline */}
                {scenario.privateTransport.routeStops.length > 1 && (
                    <Polyline
                        positions={scenario.privateTransport.routeStops}
                        color="#000000"
                        weight={3}
                        dashArray="1, 8"
                    />
                )}

                {/* Route Markers */}
                {scenario.privateTransport.routeStops.map((pos, i) => (
                    <Marker key={`stop-${i}`} position={pos} icon={L.divIcon({ className: 'bg-black w-2 h-2 border border-white' })} />
                ))}

                {/* AMTAB Overlay */}
                {scenario.publicTransportIntegration.includes('amtab') && AMTAB_STOPS.map((pos, i) => (
                    <Marker key={`amtab-${i}`} position={pos} icon={L.divIcon({ className: 'bg-black w-2 h-2 rounded-full border border-white' })} />
                ))}

                {/* Sharing Overlay */}
                {scenario.publicTransportIntegration.includes('sharing') && SHARING_NODES.map((pos, i) => (
                    <Marker key={`sharing-${i}`} position={pos} icon={L.divIcon({ className: 'bg-white w-2 h-2 rounded-full border-2 border-black' })} />
                ))}

                {/* Event Marker P */}
                <Marker position={scenario.event.location.coords}>
                    <Popup>
                        <div className="text-[10px] uppercase font-bold">{scenario.event.name || "Evento"}</div>
                    </Popup>
                </Marker>

                <Legend />
            </MapContainer>
        </div>
    );
};

export default MapView;
