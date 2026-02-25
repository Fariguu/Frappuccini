import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import type { TrafficOverlay } from '../types/scenario';
import { Slider } from './ui/slider';

const FALLBACK_HOURS = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);

interface MapViewProps {
    trafficOverlay?: TrafficOverlay | null;
    selectedHourIndex?: number;
    onHourChange?: (index: number) => void;
}

const BARI_CENTER: [number, number] = [41.1171, 16.8719];

const BARI_BOUNDS: [[number, number], [number, number]] = [
    [41.025, 16.755],
    [41.2, 16.985]
];

const Legend: React.FC<{ showTraffic?: boolean }> = ({ showTraffic }) => (
    <div className="absolute bottom-4 left-4 bg-white/90 border border-secondary/20 p-2 text-[9px] uppercase font-bold tracking-tighter z-[1000] shadow-md flex flex-col gap-1">
        <div className="flex items-center gap-2">
            <div className="w-4 h-[1px] bg-[#878787]"></div> <span>Rete stradale base</span>
        </div>
        {showTraffic ? (
            <>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-[2px] bg-[#00ff00]"></div> <span>Normale</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-[2px] bg-[#ffa500]"></div> <span>Elevato</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-[2px] bg-[#ff0000]"></div> <span>Critico</span>
                </div>
            </>
        ) : (
            <div className="flex items-center gap-2">
                <div className="w-4 h-[2px] bg-[#000000]"></div> <span>Traffico previsto</span>
            </div>
        )}
    </div>
);

const MapView: React.FC<MapViewProps> = ({
    trafficOverlay,
    selectedHourIndex = 0,
    onHourChange,
}) => {
    const [geoData, setGeoData] = useState<any>(null);
    const [backendOffline, setBackendOffline] = useState(false);

    useEffect(() => {
        (async () => {
            try {
                const response = await fetch('/api/map');
                if (!response.ok) throw new Error();
                const data = await response.json();
                if (data.error) throw new Error();
                setGeoData(data);
                setBackendOffline(false);
            } catch {
                setGeoData(null);
                setBackendOffline(true);
            }
        })();
    }, []);

    const hours = trafficOverlay?.hours ?? FALLBACK_HOURS;
    const timeStr = hours[Math.min(selectedHourIndex, hours.length - 1)];

    const streetColors = useMemo(() => {
        const colors = trafficOverlay?.by_street?.[timeStr];
        // #region agent log
        if (trafficOverlay && !colors && timeStr) {
            try {
                fetch('http://127.0.0.1:7243/ingest/f65d3bd1-4a59-47f7-8eda-a434091e96ac',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'MapView.tsx:streetColors',message:'no by_street for timeStr',data:{timeStr,availableHours:Object.keys(trafficOverlay?.by_street||{}).slice(0,8)},timestamp:Date.now(),hypothesisId:'F'})}).catch(()=>{});
            } catch (_) {}
        }
        // #endregion
        if (!colors) return null;
        return colors;
    }, [trafficOverlay, timeStr]);

    const quartiereColors = useMemo(() => {
        if (!trafficOverlay?.by_quartiere?.[timeStr]) return null;
        const qc = trafficOverlay.by_quartiere[timeStr];
        const out: Record<string, string> = {};
        for (const [k, v] of Object.entries(qc)) {
            out[k.toUpperCase().trim()] = v;
        }
        return out;
    }, [trafficOverlay, timeStr]);

    const roadStyle = (feature: any) => {
        const props = feature?.properties || {};
        const streetName: string | null = props.street_name ?? null;

        if (streetColors && streetName) {
            const color = streetColors[streetName];
            if (color) {
                const weight = color === '#ff0000' ? 3 : color === '#ffa500' ? 2.5 : 2;
                return { color, weight, opacity: 0.85 };
            }
        }

        if (quartiereColors) {
            const q1 = (props.quartiere_ ?? '').toUpperCase().trim();
            const q2 = (props.quartier_1 ?? '').toUpperCase().trim();
            const color = quartiereColors[q1] ?? quartiereColors[q2] ?? '#00ff00';
            const weight = color === '#ff0000' ? 3 : color === '#ffa500' ? 2.5 : 2;
            return { color, weight, opacity: 0.85 };
        }

        return {
            color: '#878787',
            weight: 1,
            opacity: 0.4,
        };
    };

    return (
        <div className="w-full h-full bg-background relative overflow-hidden">
            {backendOffline && (
                <div className="absolute top-4 left-4 bg-zinc-900 text-white px-3 py-1 text-[10px] font-bold z-[2000] uppercase tracking-widest shadow-lg flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
                    Dati stradali non disponibili (backend offline)
                </div>
            )}

            <div className="absolute top-4 right-4 bg-white/80 border border-secondary/20 p-2 text-[10px] font-mono uppercase tracking-widest z-[1000] shadow-sm">
                GIS View: Cartografia_Bari_v02
            </div>

            <MapContainer
                center={BARI_CENTER}
                zoom={14}
                minZoom={11}
                maxZoom={18}
                maxBounds={BARI_BOUNDS}
                maxBoundsViscosity={1}
                className="w-full h-full"
                zoomControl={false}
            >
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; OSM'
                />

                {geoData && (
                    <GeoJSON
                        key={`geo-${selectedHourIndex}-${!!trafficOverlay}`}
                        data={geoData}
                        style={roadStyle}
                    />
                )}

                <Legend showTraffic={!!trafficOverlay} />

                {trafficOverlay && onHourChange && (
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-[min(480px,92%)] bg-white/95 border border-secondary/20 p-4 rounded-lg shadow-lg z-[1000]">
                        <div className="flex items-center justify-between gap-2 mb-3">
                            <span className="text-[10px] font-bold uppercase tracking-widest text-secondary">Fascia Oraria</span>
                            <span className="text-sm font-mono font-bold tabular-nums">{timeStr}</span>
                        </div>
                        <Slider
                            min={0}
                            max={hours.length - 1}
                            step={1}
                            value={[selectedHourIndex]}
                            onValueChange={([v]) => onHourChange(v)}
                        />
                        <div className="flex justify-between mt-2 text-[9px] text-secondary">
                            {hours.map((h, i) => {
                                const showLabel = hours.length <= 8 || i % Math.ceil(hours.length / 8) === 0 || i === hours.length - 1;
                                return (
                                    <span key={h} className={`${i === selectedHourIndex ? 'font-bold text-primary' : ''} ${showLabel ? '' : 'invisible'}`}>
                                        {h.slice(0, 5)}
                                    </span>
                                );
                            })}
                        </div>
                    </div>
                )}
            </MapContainer>
        </div>
    );
};

export default MapView;
