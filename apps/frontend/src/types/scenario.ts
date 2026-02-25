export interface Location {
    streetName: string;
    coords: [number, number];
}

export interface DateRange {
    start: string;
    end: string;
}

export interface PrivateTransport {
    vehicleType: 'car' | 'bus' | 'van';
    count: number;
    capacity: number;
    routeStops: [number, number][];
}

export interface EventScenario {
    event: {
        name: string;
        guests: string[];
        location: Location;
        dateRange: DateRange;
        totalPeople: number;
    };
    privateTransport: PrivateTransport;
    publicTransportIntegration: string[];
}
