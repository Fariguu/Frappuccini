import React from 'react';

interface SidebarProps {
    eventParam: string;
    setEventParam: (val: string) => void;
    intensity: number;
    setIntensity: (val: number) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ eventParam, setEventParam, intensity, setIntensity }) => {
    return (
        <div className="w-80 h-full bg-white border-r border-secondary/20 p-6 flex flex-col gap-8 shadow-sm">
            <div className="flex flex-col gap-2">
                <h2 className="text-foreground font-bold tracking-tighter leading-none" style={{ fontSize: '1.5rem' }}>
                    CONTROL
                    <span className="block text-secondary text-sm font-medium tracking-normal mt-1">FRAPPUCCINI v1.0</span>
                </h2>
            </div>

            <div className="flex flex-col gap-6">
                <div className="space-y-2">
                    <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Parametro Evento</label>
                    <input
                        type="text"
                        value={eventParam}
                        onChange={(e) => setEventParam(e.target.value)}
                        placeholder="Es. Partita Stadio"
                        className="w-full bg-background border border-secondary/20 px-3 py-2 text-sm focus:outline-none focus:border-primary transition-colors"
                    />
                </div>

                <div className="space-y-4">
                    <div className="flex justify-between items-end">
                        <label className="text-[10px] uppercase font-bold tracking-widest text-secondary">Intensità</label>
                        <span className="text-sm font-mono font-bold">{intensity}%</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={intensity}
                        onChange={(e) => setIntensity(parseInt(e.target.value))}
                        className="w-full accent-black h-1 bg-secondary/20 rounded-lg appearance-none cursor-pointer"
                    />
                </div>
            </div>

            <div className="mt-auto space-y-4">
                <div className="p-4 bg-background border border-secondary/10">
                    <div className="text-[10px] uppercase font-bold tracking-widest text-secondary mb-1">KPI PREVISIONE</div>
                    <div className="flex justify-between items-baseline">
                        <span className="text-2xl font-mono font-bold">1.2x</span>
                        <span className="text-[10px] text-primary bg-accent px-1 font-bold italic">+20% FLOW</span>
                    </div>
                </div>

                <div className="p-4 bg-background border border-secondary/10">
                    <div className="text-[10px] uppercase font-bold tracking-widest text-secondary mb-1">STRADE COINVOLTE</div>
                    <div className="text-xl font-mono font-bold">
                        {Math.floor(intensity * 0.45)} <span className="text-xs font-sans font-normal text-secondary uppercase">nodi</span>
                    </div>
                </div>
            </div>

            <div className="pt-4 border-t border-secondary/10">
                <button className="w-full bg-primary text-white py-3 font-bold text-xs uppercase tracking-widest hover:bg-zinc-800 transition-colors">
                    Esporta Previsione
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
