export interface Location {
    coords: [number, number];
}

export interface EventData {
    name: string;
    venue: string;
    location: Location;
    date: string;
    endTime: string;
    totalPeople: number;
    guests: string[];
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export interface ExtractedParams {
    event_name: string | null;
    venue: string | null;
    date: string | null;
    end_time: string | null;
    capacity: number | null;
    vip_names: string[];
    vip_analysis: string | null;
    estimated_multiplier: number | null;
    confidence: string | null;
}

export interface ChatResponse {
    reply: string;
    extracted_params: ExtractedParams;
    ready_to_simulate: boolean;
    missing_info: string[];
}

export interface TrafficOverlay {
    hours: string[];
    by_street: Record<string, Record<string, string>>;
    by_neighborhood: Record<string, Record<string, string>>;
    by_quartiere: Record<string, Record<string, string>>;
}
