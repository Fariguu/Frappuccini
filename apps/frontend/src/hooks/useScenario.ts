import { useState, useCallback } from 'react';
import type { EventScenario, PrivateTransport } from '../types/scenario';

const INITIAL_STATE: EventScenario = {
    event: {
        name: '',
        guests: [],
        location: { streetName: '', coords: [41.1171, 16.8719] },
        dateRange: { start: '', end: '' },
        totalPeople: 0
    },
    privateTransport: {
        vehicleType: 'car',
        count: 0,
        capacity: 4,
        routeStops: []
    },
    publicTransportIntegration: []
};

export function useScenario() {
    const [scenario, setScenario] = useState<EventScenario>(INITIAL_STATE);

    const updateEvent = useCallback((updates: Partial<EventScenario['event']>) => {
        setScenario(prev => ({
            ...prev,
            event: { ...prev.event, ...updates }
        }));
    }, []);

    const updatePrivateTransport = useCallback((updates: Partial<PrivateTransport>) => {
        setScenario(prev => ({
            ...prev,
            privateTransport: { ...prev.privateTransport, ...updates }
        }));
    }, []);

    const addRouteStop = useCallback((coords: [number, number]) => {
        setScenario(prev => ({
            ...prev,
            privateTransport: {
                ...prev.privateTransport,
                routeStops: [...prev.privateTransport.routeStops, coords]
            }
        }));
    }, []);

    const clearRoute = useCallback(() => {
        setScenario(prev => ({
            ...prev,
            privateTransport: { ...prev.privateTransport, routeStops: [] }
        }));
    }, []);

    const togglePublicIntegration = useCallback((service: string) => {
        setScenario(prev => {
            const exists = prev.publicTransportIntegration.includes(service);
            const next = exists
                ? prev.publicTransportIntegration.filter(s => s !== service)
                : [...prev.publicTransportIntegration, service];
            return { ...prev, publicTransportIntegration: next };
        });
    }, []);

    const generateJson = useCallback(() => {
        console.log('GENERATE SCENARIO JSON:', JSON.stringify(scenario, null, 2));
        alert('Configurazione Scenario esportata in Console (F12)');
    }, [scenario]);

    return {
        scenario,
        updateEvent,
        updatePrivateTransport,
        togglePublicIntegration,
        addRouteStop,
        clearRoute,
        generateJson
    };
}
