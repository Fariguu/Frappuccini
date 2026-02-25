import React, { useState } from 'react';
import type { EventScenario } from '../types/scenario';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Checkbox } from './ui/checkbox';
import { Card, CardFooter, CardHeader } from './ui/card';

export type Tab = 'EVENT' | 'PRIVATE' | 'PUBLIC';

interface SidebarProps {
    scenario: EventScenario;
    activeTab: Tab;
    onTabChange: (tab: Tab) => void;
    onUpdateEvent: (updates: Partial<EventScenario['event']>) => void;
    onUpdatePrivate: (updates: Partial<EventScenario['privateTransport']>) => void;
    onTogglePublic: (service: string) => void;
    onClearRoute: () => void;
    onSimulate: () => void;
    simulateLoading?: boolean;
    simulateError?: string | null;
    onTest?: () => void;
}

const END_TIME_OPTIONS = [
    '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
];

const Sidebar: React.FC<SidebarProps> = ({
    scenario,
    activeTab,
    onTabChange,
    onUpdateEvent,
    onUpdatePrivate,
    onTogglePublic,
    onClearRoute,
    onSimulate,
    simulateLoading,
    simulateError,
    onTest
}) => {
    const [vipInput, setVipInput] = useState('');

    const handleAddVip = () => {
        const name = vipInput.trim();
        if (name && !scenario.event.guests.includes(name)) {
            onUpdateEvent({ guests: [...scenario.event.guests, name] });
        }
        setVipInput('');
    };

    const handleRemoveVip = (name: string) => {
        onUpdateEvent({ guests: scenario.event.guests.filter(g => g !== name) });
    };

    return (
        <Card className="relative z-10 shrink-0 w-80 h-full rounded-none border-r border-border flex flex-col gap-0 py-0 shadow-sm overflow-hidden bg-white">
            <CardHeader className="p-6 border-b border-border flex flex-row justify-between items-center space-y-0">
                <div>
                    <h2 className="text-foreground font-bold tracking-tighter leading-none text-lg">
                        CONFIGURATORE
                        <span className="block text-muted-foreground text-xs font-medium tracking-normal mt-1 italic">SCENARIO v2.0</span>
                    </h2>
                </div>
                <Button
                    variant="outline"
                    size="xs"
                    onClick={onTest}
                    className="uppercase"
                >
                    test
                </Button>
            </CardHeader>

            <Tabs value={activeTab} onValueChange={(v) => onTabChange(v as Tab)} className="flex-1 flex flex-col min-h-0 gap-0">
                <TabsList className="w-full rounded-none border-b border-border bg-transparent h-auto p-0 gap-0 shrink-0">
                    {(['EVENT', 'PRIVATE', 'PUBLIC'] as Tab[]).map((tab) => (
                        <TabsTrigger
                            key={tab}
                            value={tab}
                            className="flex-1 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-accent/10 data-[state=active]:text-foreground text-muted-foreground text-xs font-bold uppercase tracking-widest py-3"
                        >
                            {tab === 'EVENT' ? 'Evento' : tab === 'PRIVATE' ? 'Privata' : 'Pubblica'}
                        </TabsTrigger>
                    ))}
                </TabsList>

                <TabsContent value="EVENT" className="flex-1 overflow-y-auto p-6 mt-0 data-[state=inactive]:hidden">
                    <div className="space-y-5 animate-in fade-in slide-in-from-left-2 duration-300">
                        <div className="space-y-2">
                            <Label className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Posizione Evento</Label>
                            <p className="text-xs text-muted-foreground italic">
                                Clicca sulla mappa per impostare la posizione dell&apos;evento
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="event-name" className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Nome Evento</Label>
                            <Input
                                id="event-name"
                                type="text"
                                value={scenario.event.name}
                                onChange={(e) => onUpdateEvent({ name: e.target.value })}
                                placeholder="Es. Concerto Stadio"
                                className="text-foreground bg-white"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="event-venue" className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Luogo / Venue</Label>
                            <Input
                                id="event-venue"
                                type="text"
                                value={scenario.event.venue}
                                onChange={(e) => onUpdateEvent({ venue: e.target.value })}
                                placeholder="Es. Stadio San Nicola, Bari"
                                className="text-foreground bg-white"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="event-date" className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Data Evento</Label>
                            <Input
                                id="event-date"
                                type="date"
                                value={scenario.event.dateRange.start}
                                min={new Date().toISOString().split('T')[0]}
                                onChange={(e) => onUpdateEvent({ dateRange: { ...scenario.event.dateRange, start: e.target.value } })}
                                className="text-foreground bg-white"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="event-end-time" className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Orario Fine Evento</Label>
                            <Select
                                value={scenario.event.endTime}
                                onValueChange={(v) => onUpdateEvent({ endTime: v })}
                            >
                                <SelectTrigger className="w-full text-foreground bg-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {END_TIME_OPTIONS.map((t) => (
                                        <SelectItem key={t} value={t}>{t}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="total-people" className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Capacit&agrave; / Partecipanti</Label>
                            <Input
                                id="total-people"
                                type="number"
                                value={scenario.event.totalPeople}
                                onChange={(e) => onUpdateEvent({ totalPeople: parseInt(e.target.value) || 0 })}
                                placeholder="Numero partecipanti..."
                                className="text-foreground bg-white"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Ospiti VIP</Label>
                            <div className="flex gap-2">
                                <Input
                                    type="text"
                                    value={vipInput}
                                    onChange={(e) => setVipInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleAddVip()}
                                    placeholder="Nome ospite..."
                                    className="text-foreground bg-white flex-1"
                                />
                                <Button variant="outline" size="sm" onClick={handleAddVip} className="shrink-0">
                                    +
                                </Button>
                            </div>
                            {scenario.event.guests.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 mt-2">
                                    {scenario.event.guests.map((g) => (
                                        <span
                                            key={g}
                                            className="inline-flex items-center gap-1 bg-accent/20 text-foreground text-[10px] font-bold uppercase tracking-wide px-2 py-1 rounded cursor-pointer hover:bg-destructive/20 hover:text-destructive transition-colors"
                                            onClick={() => handleRemoveVip(g)}
                                            title="Clicca per rimuovere"
                                        >
                                            {g} &times;
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="PRIVATE" className="flex-1 overflow-y-auto p-6 mt-0 data-[state=inactive]:hidden">
                    <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-300">
                        <div className="space-y-2">
                            <Label className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Mezzo Prevalente</Label>
                            <Select
                                value={scenario.privateTransport.vehicleType}
                                onValueChange={(v) => onUpdatePrivate({ vehicleType: v as any })}
                            >
                                <SelectTrigger className="w-full text-foreground bg-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="car">Auto</SelectItem>
                                    <SelectItem value="bus">Bus Turistici</SelectItem>
                                    <SelectItem value="van">Van</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label className="text-xs uppercase font-bold tracking-widest text-muted-foreground">Pianificatore Tratta</Label>
                            <Button
                                variant="outline"
                                onClick={onClearRoute}
                                className="w-full border-2 border-dashed py-4 h-auto flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground hover:bg-accent/10"
                            >
                                {scenario.privateTransport.routeStops.length > 0
                                    ? (
                                        <>
                                            <span className="font-bold uppercase">{scenario.privateTransport.routeStops.length} Fermate definite</span>
                                            <span className="text-destructive text-[10px] font-medium">Clicca per resettare</span>
                                        </>
                                    )
                                    : <span className="font-bold uppercase">Clicca sulla mappa per definire fermate</span>}
                            </Button>
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="PUBLIC" className="flex-1 overflow-y-auto p-6 mt-0 data-[state=inactive]:hidden">
                    <div className="space-y-4 animate-in fade-in slide-in-from-left-2 duration-300">
                        <p className="text-xs text-muted-foreground leading-relaxed mb-4 font-medium uppercase tracking-tight">
                            Seleziona i servizi pubblici da integrare per ridurre l&apos;impatto sulla viabilità.
                        </p>
                        {[
                            { id: 'amtab', label: 'AMTAB (GTFS)' },
                            { id: 'park-and-ride', label: 'Park & Ride' },
                            { id: 'sharing', label: 'Bike/Monopattini Sharing' }
                        ].map((item) => (
                            <label
                                key={item.id}
                                className="flex items-center gap-3 p-3 rounded-md border border-border bg-white cursor-pointer hover:bg-accent/10 hover:border-accent transition-colors group"
                            >
                                <Checkbox
                                    checked={scenario.publicTransportIntegration.includes(item.id)}
                                    onCheckedChange={() => onTogglePublic(item.id)}
                                />
                                <span className="text-xs font-bold uppercase text-foreground group-hover:text-primary transition-colors">{item.label}</span>
                            </label>
                        ))}
                    </div>
                </TabsContent>
            </Tabs>

            {/* Footer */}
            <CardFooter className="p-6 border-t border-border flex flex-col gap-3 bg-white">
                <div className="flex justify-between items-baseline mb-2">
                    <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Previsione</span>
                    <span className="text-xl font-mono font-bold italic uppercase leading-none text-foreground">Live</span>
                </div>
                {simulateError && (
                    <p className="text-xs text-destructive font-medium">{simulateError}</p>
                )}
                <Button
                    onClick={onSimulate}
                    disabled={simulateLoading}
                    className="w-full uppercase tracking-widest"
                >
                    {simulateLoading ? 'Simulazione...' : 'Simula Traffico'}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default Sidebar;
