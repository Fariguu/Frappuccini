import React, { useState } from 'react';
import type { EventScenario } from '../types/scenario';

type Tab = 'EVENT' | 'PRIVATE' | 'PUBLIC';

interface SidebarProps {
    scenario: EventScenario;
    onUpdateEvent: (updates: Partial<EventScenario['event']>) => void;
    onUpdatePrivate: (updates: Partial<EventScenario['privateTransport']>) => void;
    onTogglePublic: (service: string) => void;
    onClearRoute: () => void;
    onGenerate: () => void;
    onTest?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    scenario,
    onUpdateEvent,
    onUpdatePrivate,
    onTogglePublic,
    onClearRoute,
    onGenerate,
    onTest
}) => {
    const [activeTab, setActiveTab] = useState<Tab>('EVENT');

    return (
        <div className="w-80 h-full bg-white border-r border-secondary/20 flex flex-col shadow-sm overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-secondary/10 flex justify-between items-center">
                <div>
                    <h2 className="text-foreground font-bold tracking-tighter leading-none" style={{ fontSize: '1.25rem' }}>
                        CONFIGURATORE
                        <span className="block text-secondary text-[10px] font-medium tracking-normal mt-1 italic">SCENARIO v2.0</span>
                    </h2>
                </div>
                <button
                    onClick={onTest}
                    className="bg-zinc-100 hover:bg-zinc-200 text-[10px] font-bold px-2 py-1 border border-zinc-300 transition-colors uppercase"
                >
                    test
                </button>
            </div>

            {/* Tabs Navigation */}
            <div className="flex border-b border-secondary/10">
                {(['EVENT', 'PRIVATE', 'PUBLIC'] as Tab[]).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`flex-1 py-3 text-[9px] font-bold uppercase tracking-widest transition-all ${activeTab === tab
                                ? 'text-primary bg-zinc-50 border-b-2 border-primary'
                                : 'text-secondary hover:text-primary'
                            }`}
                    >
                        {tab === 'EVENT' ? 'Evento' : tab === 'PRIVATE' ? 'Privata' : 'Pubblica'}
                    </button>
                ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {activeTab === 'EVENT' && (
                    <div className="animate-in fade-in slide-in-from-left-2 duration-300 space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Posizione Evento $P$</label>
                            <input
                                type="text"
                                value={scenario.event.location.streetName}
                                onChange={(e) => onUpdateEvent({ location: { ...scenario.event.location, streetName: e.target.value } })}
                                placeholder="Cerca via nello Stradario..."
                                className="w-full bg-background border border-secondary/20 px-3 py-2 text-xs focus:outline-none focus:border-primary"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Nome Evento</label>
                            <input
                                type="text"
                                value={scenario.event.name}
                                onChange={(e) => onUpdateEvent({ name: e.target.value })}
                                placeholder="Es. Concerto Stadio"
                                className="w-full bg-background border border-secondary/20 px-3 py-2 text-xs focus:outline-none focus:border-primary"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Target Partecipanti $N$</label>
                            <input
                                type="number"
                                value={scenario.event.totalPeople}
                                onChange={(e) => onUpdateEvent({ totalPeople: parseInt(e.target.value) || 0 })}
                                placeholder="Numero partecipanti..."
                                className="w-full bg-background border border-secondary/20 px-3 py-2 text-xs focus:outline-none focus:border-primary"
                            />
                        </div>
                    </div>
                )}

                {activeTab === 'PRIVATE' && (
                    <div className="animate-in fade-in slide-in-from-left-2 duration-300 space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Mezzo Prevalente</label>
                            <select
                                value={scenario.privateTransport.vehicleType}
                                onChange={(e) => onUpdatePrivate({ vehicleType: e.target.value as any })}
                                className="w-full bg-background border border-secondary/20 px-3 py-2 text-xs focus:outline-none focus:border-primary"
                            >
                                <option value="car">Auto</option>
                                <option value="bus">Bus Turistici</option>
                                <option value="van">Van</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Pianificatore Tratta</label>
                            <button
                                onClick={onClearRoute}
                                className="w-full border-2 border-dashed border-secondary/30 py-4 text-[10px] font-bold text-secondary uppercase hover:bg-zinc-50 transition-colors group flex flex-col items-center gap-1"
                            >
                                {scenario.privateTransport.routeStops.length > 0
                                    ? (
                                        <>
                                            <span>{scenario.privateTransport.routeStops.length} Fermate definite</span>
                                            <span className="text-[8px] text-red-500 group-hover:underline">Clicca per resettare</span>
                                        </>
                                    )
                                    : <span>Clicca sulla mappa per definire fermate</span>}
                            </button>
                        </div>
                    </div>
                )}

                {activeTab === 'PUBLIC' && (
                    <div className="animate-in fade-in slide-in-from-left-2 duration-300 space-y-4">
                        <p className="text-[10px] text-secondary leading-relaxed mb-4 font-medium uppercase tracking-tight">
                            Seleziona i servizi pubblici da integrare per ridurre l'impatto sulla viabilità.
                        </p>
                        {[
                            { id: 'amtab', label: 'AMTAB (GTFS)' },
                            { id: 'park-and-ride', label: 'Park & Ride' },
                            { id: 'sharing', label: 'Bike/Monopattini Sharing' }
                        ].map((item) => (
                            <label key={item.id} className="flex items-center gap-3 p-3 bg-zinc-50 border border-secondary/10 cursor-pointer hover:border-secondary transition-colors group">
                                <input
                                    type="checkbox"
                                    checked={scenario.publicTransportIntegration.includes(item.id)}
                                    onChange={() => onTogglePublic(item.id)}
                                    className="accent-black"
                                />
                                <span className="text-[10px] font-bold uppercase group-hover:text-primary transition-colors">{item.label}</span>
                            </label>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-6 bg-zinc-50 border-t border-secondary/10 flex flex-col gap-3">
                <div className="flex justify-between items-baseline mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-secondary">Previsione</span>
                    <span className="text-xl font-mono font-bold italic uppercase leading-none">Live</span>
                </div>
                <button
                    onClick={onGenerate}
                    className="w-full bg-primary text-white py-3 font-bold text-xs uppercase tracking-widest hover:bg-zinc-800 transition-colors shadow-lg active:scale-[0.98]"
                >
                    Genera Scenario JSON
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
