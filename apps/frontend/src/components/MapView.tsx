import React from 'react';

interface MapViewProps {
    intensity: number;
}

const MapView: React.FC<MapViewProps> = ({ intensity }) => {
    // Mock data for streets (Bari-like grid)
    const baseStreets = [
        { id: 's1', d: 'M 50 100 L 450 100' },
        { id: 's2', d: 'M 50 200 L 450 200' },
        { id: 's3', d: 'M 50 300 L 450 300' },
        { id: 's4', d: 'M 100 50 L 100 450' },
        { id: 's5', d: 'M 200 50 L 200 450' },
        { id: 's6', d: 'M 300 50 L 300 450' },
        { id: 's7', d: 'M 400 50 L 400 450' },
    ];

    // Mock AMTAB stops
    const amtabStops = [
        { cx: 100, cy: 100 },
        { cx: 200, cy: 200 },
        { cx: 300, cy: 300 },
        { cx: 400, cy: 100 },
    ];

    // Mock Bike Sharing stations
    const bikeStations = [
        { cx: 150, cy: 150 },
        { cx: 250, cy: 250 },
        { cx: 350, cy: 150 },
    ];

    // Dynamic segments (the ones that change)
    const dynamicSegments = [
        { id: 'd1', d: 'M 100 200 L 200 200', threshold: 20 },
        { id: 'd2', d: 'M 200 200 L 300 200', threshold: 50 },
        { id: 'd3', d: 'M 300 200 L 400 200', threshold: 70 },
        { id: 'd4', d: 'M 200 100 L 200 200', threshold: 30 },
        { id: 'd5', d: 'M 200 200 L 200 300', threshold: 60 },
    ];

    return (
        <div className="flex-1 bg-background relative overflow-hidden flex items-center justify-center p-8">
            <div className="absolute top-4 right-4 bg-white/80 border border-secondary/20 p-2 text-[10px] font-mono uppercase tracking-widest z-10 shadow-sm">
                Map View: Bari_metropolitan_v01
            </div>

            <svg
                viewBox="0 0 500 500"
                className="w-full h-full max-w-4xl drop-shadow-2xl"
                style={{ filter: 'grayscale(0.2)' }}
            >
                {/* Base Layer: Streets */}
                <g id="base-layer">
                    {baseStreets.map((s) => (
                        <path
                            key={s.id}
                            d={s.d}
                            stroke="#878787"
                            strokeWidth="1"
                            strokeLinecap="round"
                            fill="none"
                            className="transition-all duration-700 opacity-30"
                        />
                    ))}
                </g>

                {/* Dynamic Layer: Predicted Traffic */}
                <g id="dynamic-layer">
                    {dynamicSegments.map((s) => {
                        const isActive = intensity >= s.threshold;
                        return (
                            <path
                                key={s.id}
                                d={s.d}
                                stroke={isActive ? '#000000' : '#878787'}
                                strokeWidth={isActive ? (2 + intensity / 20) : "1"}
                                strokeLinecap="round"
                                fill="none"
                                className="transition-all duration-500 ease-out"
                                style={{ opacity: isActive ? 1 : 0.2 }}
                            />
                        );
                    })}
                </g>

                {/* Transport Layer: Points of Interest */}
                <g id="transport-layer">
                    {/* AMTAB Stops */}
                    {amtabStops.map((p, i) => (
                        <circle
                            key={`amtab-${i}`}
                            cx={p.cx}
                            cy={p.cy}
                            r="3"
                            fill="#000000"
                            className="hover:scale-150 transition-transform cursor-pointer"
                        />
                    ))}
                    {/* Bike Sharing */}
                    {bikeStations.map((p, i) => (
                        <circle
                            key={`bike-${i}`}
                            cx={p.cx}
                            cy={p.cy}
                            r="4"
                            fill="#ffffff"
                            stroke="#000000"
                            strokeWidth="1"
                            className="hover:scale-150 transition-transform cursor-pointer"
                        />
                    ))}
                </g>
            </svg>

            {/* Legend Overlay */}
            <div className="absolute bottom-4 left-4 flex flex-col gap-1 text-[9px] uppercase font-bold tracking-tighter">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-[1px] bg-[#878787]"></div> <span>Rete stradale base</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-[2px] bg-[#000000]"></div> <span>Traffico previsto</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-black"></div> <span>Fermate AMTAB</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-white border border-black"></div> <span>Bike Sharing</span>
                </div>
            </div>
        </div>
    );
};

export default MapView;
