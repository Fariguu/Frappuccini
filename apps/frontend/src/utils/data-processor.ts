/**
 * Utilities for processing Bari Open Data into SVG components.
 */

export interface GeoPoint {
    lat: number;
    lng: number;
}

export interface StreetSegment {
    id: string;
    points: GeoPoint[];
    importance: number; // 0-1
}

/**
 * Normalizes coordinates to fit within a given SVG viewBox.
 * (Simple linear projection for demonstration)
 */
export const normalizeToViewBox = (
    points: GeoPoint[],
    viewBox: { width: number; height: number },
    bounds: { minLat: number; maxLat: number; minLng: number; maxLng: number }
) => {
    return points.map(p => ({
        x: ((p.lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * viewBox.width,
        y: viewBox.height - ((p.lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * viewBox.height
    }));
};

/**
 * Converts normalized points to an SVG path string.
 */
export const pointsToPath = (points: { x: number; y: number }[]) => {
    if (points.length < 2) return '';
    const [first, ...rest] = points;
    return `M ${first.x.toFixed(2)} ${first.y.toFixed(2)} ` +
        rest.map(p => `L ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ');
};

/**
 * Hypothetical parser for AMTAB GTFS data or CSV.
 */
export const parsePOI = (data: any[]): GeoPoint[] => {
    return data.map(item => ({
        lat: parseFloat(item.lat || item.latitude),
        lng: parseFloat(item.lng || item.longitude)
    }));
};
