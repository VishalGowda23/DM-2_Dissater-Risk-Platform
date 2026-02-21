import { useState, useEffect } from 'react';
import { Navigation, MapPin, Shield, Clock, Users } from 'lucide-react';
import { API_BASE_URL, getRiskColor, type Shelter } from '@/lib/types';

interface ShelterRoute {
    shelter: Shelter;
    distance_km: number;
    travel_time_min: number;
    route_safety: { safety_score: number; status: string; avoid_roads: string[]; safe_alternatives?: string[] };
    route_coords: number[][];
    score: number;
}

interface EvacRoute {
    ward_id: string;
    ward_name: string;
    ward_centroid: { lat: number; lon: number };
    risk_level: number;
    recommended_shelter: ShelterRoute | null;
    alternatives: (ShelterRoute | null)[];
    evacuation_urgency: string;
}

interface Props {
    riskData: unknown[];
    wards: unknown[];
}

export default function EvacuationMap(_props: Props) {
    const [routes, setRoutes] = useState<EvacRoute[]>([]);
    const [shelters, setShelters] = useState<Shelter[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedRoute, setSelectedRoute] = useState<EvacRoute | null>(null);
    const [filterUrgency, setFilterUrgency] = useState<string>('all');

    const fetchRoutes = async () => {
        setLoading(true);
        try {
            const [routeRes, shelterRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/evacuation`),
                fetch(`${API_BASE_URL}/api/shelters`),
            ]);
            const routeData = await routeRes.json();
            const shelterData = await shelterRes.json();
            setRoutes(routeData.routes || []);
            setShelters(shelterData.shelters || []);
        } catch (err) {
            console.error('Failed to fetch evacuation data:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchRoutes(); }, []);

    const getUrgencyStyle = (u: string) => {
        const styles: Record<string, string> = {
            immediate: 'bg-red-600 text-white',
            prepare: 'bg-orange-500 text-white',
            monitor: 'bg-yellow-500 text-black',
            standby: 'bg-green-500 text-white',
        };
        return styles[u] || 'bg-gray-500 text-white';
    };

    const getSafetyStyle = (s: string) => {
        if (s === 'safe') return 'text-green-600';
        if (s === 'moderate_risk') return 'text-yellow-600';
        return 'text-red-600';
    };

    const filtered = filterUrgency === 'all' ? routes : routes.filter(r => r.evacuation_urgency === filterUrgency);

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="bg-white border-2 border-black p-4 flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-black flex items-center gap-2">
                        <Navigation className="w-6 h-6" />
                        Evacuation Route Optimizer
                    </h2>
                    <p className="text-sm text-gray-500">Safe routes to nearest shelters, dynamically avoiding flood-prone roads</p>
                </div>
                <button onClick={fetchRoutes} className="bg-black text-white px-4 py-2 font-bold text-sm">
                    {loading ? 'Loading...' : 'Compute Routes'}
                </button>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2">
                {['all', 'immediate', 'prepare', 'monitor', 'standby'].map(u => (
                    <button
                        key={u}
                        onClick={() => setFilterUrgency(u)}
                        className={`px-3 py-1 text-sm font-bold border-2 transition-all ${filterUrgency === u ? 'bg-black text-white border-black' : 'border-gray-300 hover:border-black'
                            }`}
                    >
                        {u.toUpperCase()} ({u === 'all' ? routes.length : routes.filter(r => r.evacuation_urgency === u).length})
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-12 gap-4">
                {/* Route List */}
                <div className="col-span-5 bg-white border-2 border-black overflow-hidden" style={{ maxHeight: 'calc(100vh - 340px)' }}>
                    <div className="p-3 bg-black text-white font-black text-sm uppercase">
                        Ward Evacuation Routes ({filtered.length})
                    </div>
                    <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 400px)' }}>
                        {filtered.map(route => (
                            <div
                                key={route.ward_id}
                                onClick={() => setSelectedRoute(route)}
                                className={`p-3 border-b-2 cursor-pointer hover:bg-gray-50 transition-colors ${selectedRoute?.ward_id === route.ward_id ? 'bg-gray-100 border-l-4 border-l-black' : ''
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-sm">{route.ward_name}</span>
                                    <span className={`text-xs px-2 py-0.5 font-bold ${getUrgencyStyle(route.evacuation_urgency)}`}>
                                        {route.evacuation_urgency.toUpperCase()}
                                    </span>
                                </div>
                                {route.recommended_shelter && (
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-1 text-xs text-gray-600">
                                            <MapPin className="w-3 h-3" />
                                            {route.recommended_shelter.shelter.name}
                                        </div>
                                        <div className="flex items-center gap-3 text-xs text-gray-500">
                                            <span>📏 {route.recommended_shelter.distance_km}km</span>
                                            <span>⏱️ {route.recommended_shelter.travel_time_min}min walk</span>
                                            <span className={getSafetyStyle(route.recommended_shelter.route_safety.status)}>
                                                🛡️ {route.recommended_shelter.route_safety.status}
                                            </span>
                                        </div>
                                        {route.recommended_shelter.route_safety.avoid_roads.length > 0 && (
                                            <div className="text-xs text-red-600 font-bold">
                                                ⚠ Avoid: {route.recommended_shelter.route_safety.avoid_roads.join(', ')}
                                            </div>
                                        )}
                                    </div>
                                )}
                                <div className="mt-1">
                                    <div className="w-full bg-gray-200 h-1">
                                        <div
                                            className="h-1"
                                            style={{
                                                width: `${route.risk_level}%`,
                                                backgroundColor: getRiskColor(route.risk_level)
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Detail Panel */}
                <div className="col-span-7 space-y-4">
                    {selectedRoute ? (
                        <>
                            {/* Ward Info */}
                            <div className="bg-white border-2 border-black p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-xl font-black">{selectedRoute.ward_name}</h3>
                                        <div className="text-sm text-gray-500">
                                            Risk Level: <span className="font-bold" style={{ color: getRiskColor(selectedRoute.risk_level) }}>{selectedRoute.risk_level}%</span>
                                        </div>
                                    </div>
                                    <div className={`text-lg px-4 py-2 font-black ${getUrgencyStyle(selectedRoute.evacuation_urgency)}`}>
                                        {selectedRoute.evacuation_urgency === 'immediate' ? '🚨 EVACUATE NOW' :
                                            selectedRoute.evacuation_urgency === 'prepare' ? '⚠️ PREPARE' :
                                                selectedRoute.evacuation_urgency === 'monitor' ? '👀 MONITOR' : '✅ STANDBY'}
                                    </div>
                                </div>
                            </div>

                            {/* Recommended Shelter */}
                            {selectedRoute.recommended_shelter && (
                                <div className="bg-green-50 border-2 border-green-500 p-4">
                                    <div className="flex items-center gap-2 mb-3">
                                        <Shield className="w-5 h-5 text-green-600" />
                                        <h4 className="font-black text-sm uppercase">Recommended Shelter</h4>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <div className="text-lg font-black">{selectedRoute.recommended_shelter.shelter.icon} {selectedRoute.recommended_shelter.shelter.name}</div>
                                            <div className="text-sm text-gray-600 mt-1">Type: {selectedRoute.recommended_shelter.shelter.type.replace('_', ' ')}</div>
                                            <div className="flex items-center gap-2 mt-2 text-sm">
                                                <Users className="w-4 h-4" />
                                                Capacity: <span className="font-bold">{selectedRoute.recommended_shelter.shelter.capacity}</span>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2 text-sm">
                                                <Navigation className="w-4 h-4" />
                                                Distance: <span className="font-bold">{selectedRoute.recommended_shelter.distance_km}km</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-sm">
                                                <Clock className="w-4 h-4" />
                                                Walking: <span className="font-bold">{selectedRoute.recommended_shelter.travel_time_min} min</span>
                                            </div>
                                            <div className={`text-sm font-bold ${getSafetyStyle(selectedRoute.recommended_shelter.route_safety.status)}`}>
                                                Route Safety: {selectedRoute.recommended_shelter.route_safety.safety_score * 100}% ({selectedRoute.recommended_shelter.route_safety.status})
                                            </div>
                                        </div>
                                    </div>
                                    <div className="mt-3 flex flex-wrap gap-1">
                                        {selectedRoute.recommended_shelter.shelter.facilities.map(f => (
                                            <span key={f} className="bg-green-100 text-green-800 text-xs px-2 py-0.5 font-bold">
                                                {f}
                                            </span>
                                        ))}
                                    </div>
                                    {selectedRoute.recommended_shelter.route_safety.avoid_roads.length > 0 && (
                                        <div className="mt-3 bg-red-100 p-2 text-sm text-red-700">
                                            <span className="font-bold">⚠️ Avoid these roads (flood-prone):</span>{' '}
                                            {selectedRoute.recommended_shelter.route_safety.avoid_roads.join(', ')}
                                        </div>
                                    )}
                                    {(selectedRoute.recommended_shelter.route_safety.safe_alternatives ?? []).length > 0 && (
                                        <div className="mt-2 bg-green-100 p-2 text-sm text-green-700">
                                            <span className="font-bold">✅ Use instead:</span>{' '}
                                            {(selectedRoute.recommended_shelter.route_safety.safe_alternatives ?? []).join(', ')}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Alternative Shelters */}
                            {selectedRoute.alternatives && selectedRoute.alternatives.length > 0 && (
                                <div className="bg-white border-2 border-black overflow-hidden">
                                    <div className="p-3 bg-gray-800 text-white font-black text-sm uppercase">
                                        Alternative Shelters
                                    </div>
                                    {selectedRoute.alternatives.map((alt: ShelterRoute | null, i: number) => alt && (
                                        <div key={i} className="p-3 border-b border-gray-200">
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <span className="font-bold text-sm">{alt.shelter.icon} {alt.shelter.name}</span>
                                                    <div className="text-xs text-gray-500">
                                                        {alt.distance_km}km • {alt.travel_time_min}min walk • Cap: {alt.shelter.capacity}
                                                    </div>
                                                </div>
                                                <span className={`text-xs font-bold ${getSafetyStyle(alt.route_safety.status)}`}>
                                                    {alt.route_safety.status}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="bg-white border-2 border-black p-12 text-center text-gray-500">
                            <Navigation className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p className="font-bold">Select a ward to view its evacuation route</p>
                        </div>
                    )}

                    {/* All Shelters Grid */}
                    <div className="bg-white border-2 border-black overflow-hidden">
                        <div className="p-3 bg-black text-white font-black text-sm uppercase">
                            All Shelters ({shelters.length})
                        </div>
                        <div className="grid grid-cols-3 gap-2 p-3 overflow-auto" style={{ maxHeight: 200 }}>
                            {shelters.map(s => (
                                <div key={s.id} className="border border-gray-200 p-2 text-xs">
                                    <div className="font-bold">{s.icon} {s.name}</div>
                                    <div className="text-gray-500">Cap: {s.capacity} | {s.ward_id}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
