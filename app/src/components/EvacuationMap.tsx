import { useState, useEffect, useRef, useCallback } from 'react';
import {
    Navigation, MapPin, Shield, Clock, Users, AlertTriangle,
    Radio, TrendingUp, Zap, Eye, RefreshCw, Activity, PersonStanding
} from 'lucide-react';
import {
    MapContainer, TileLayer, CircleMarker, Polyline, Popup,
    Tooltip, useMap, Marker
} from 'react-leaflet';
import L from 'leaflet';
import { API_BASE_URL, getRiskColor, type Shelter } from '@/lib/types';
import { useLang, wardName, urgencyKey, safetyStatusKey } from '@/lib/i18n';

// Fix Leaflet default icon paths broken by bundlers
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// ─── Catmull-Rom spline densification ─────────────────────────────────────
// Generates `steps` interpolated points between p1 and p2 given neighbours p0/p3
function catmullRomSegment(
    p0: [number, number], p1: [number, number],
    p2: [number, number], p3: [number, number],
    steps: number
): [number, number][] {
    const pts: [number, number][] = [];
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const t2 = t * t;
        const t3 = t2 * t;
        const lat = 0.5 * (
            2 * p1[0] +
            (-p0[0] + p2[0]) * t +
            (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
            (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
        );
        const lng = 0.5 * (
            2 * p1[1] +
            (-p0[1] + p2[1]) * t +
            (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
            (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
        );
        pts.push([lat, lng]);
    }
    return pts;
}

function densifyCoords(coords: [number, number][], stepsPerSegment = 30): [number, number][] {
    if (coords.length < 2) return coords;
    const result: [number, number][] = [];
    // Clamp-duplicate endpoints so Catmull-Rom covers full range
    const pts: [number, number][] = [coords[0], ...coords, coords[coords.length - 1]];
    for (let i = 1; i < pts.length - 2; i++) {
        const seg = catmullRomSegment(pts[i - 1], pts[i], pts[i + 1], pts[i + 2], stepsPerSegment);
        // Skip last point of each segment to avoid duplicates (except the final segment)
        const slice = i < pts.length - 3 ? seg.slice(0, -1) : seg;
        result.push(...slice);
    }
    return result;
}

// ─── Time-based animated dot ────────────────────────────────────────────────
function AnimatedRouteDot({ coords, durationMs = 7000 }: { coords: [number, number][]; durationMs?: number }) {
    const map = useMap();
    const frameRef = useRef<number>(0);
    const startTsRef = useRef<number>(-1);

    useEffect(() => {
        if (coords.length < 2) return;
        startTsRef.current = -1;

        const icon = L.divIcon({
            className: '',
            html: `<div style="width:16px;height:16px;background:#ef4444;border:3px solid white;border-radius:50%;box-shadow:0 0 12px rgba(239,68,68,0.9);animation:pulse-dot 1.2s ease-in-out infinite"></div>`,
            iconAnchor: [8, 8],
        });
        const marker = L.marker(coords[0], { icon, zIndexOffset: 2000 }).addTo(map);
        const n = coords.length - 1;

        const animate = (ts: number) => {
            if (startTsRef.current < 0) startTsRef.current = ts;
            const elapsed = (ts - startTsRef.current) % durationMs;
            const progress = (elapsed / durationMs) * n;   // 0 → n, then resets

            const idx = Math.min(Math.floor(progress), n - 1);
            const frac = progress - idx;
            const from = coords[idx];
            const to = coords[idx + 1] ?? coords[n];
            const lat = from[0] + (to[0] - from[0]) * frac;
            const lng = from[1] + (to[1] - from[1]) * frac;
            marker.setLatLng([lat, lng]);
            frameRef.current = requestAnimationFrame(animate);
        };
        frameRef.current = requestAnimationFrame(animate);

        return () => {
            cancelAnimationFrame(frameRef.current);
            marker.remove();
        };
    }, [coords, durationMs, map]);

    return null;
}

// ─── Pulsing circle overlay for flood simulation ───────────────────────────
function PulsingRiskOverlay({ routes, floodMode }: { routes: EvacRoute[]; floodMode: boolean }) {
    const map = useMap();
    const layerRef = useRef<L.LayerGroup | null>(null);
    const animFrameRef = useRef<number>(0);

    useEffect(() => {
        if (!floodMode) {
            layerRef.current?.clearLayers();
            cancelAnimationFrame(animFrameRef.current);
            return;
        }

        const group = L.layerGroup().addTo(map);
        layerRef.current = group;

        const highRisk = routes.filter(r => r.risk_level > 30);
        const circles = highRisk.map(r =>
            L.circle([r.ward_centroid.lat, r.ward_centroid.lon], {
                radius: 200,
                color: '#ef4444',
                fillColor: '#ef4444',
                fillOpacity: 0.3,
                weight: 2,
                opacity: 0.8,
            }).addTo(group)
        );

        let startTs = -1;
        const animate = (ts: number) => {
            if (startTs < 0) startTs = ts;
            const t = ((ts - startTs) / 1000) * 1.5; // ~1.5 radians per second
            circles.forEach((c, i) => {
                const base = 200 + highRisk[i].risk_level * 3;
                c.setRadius(base * (1 + 0.45 * Math.sin(t + i * 0.8)));
                c.setStyle({ fillOpacity: 0.1 + 0.18 * Math.abs(Math.sin(t + i)) });
            });
            animFrameRef.current = requestAnimationFrame(animate);
        };
        animFrameRef.current = requestAnimationFrame(animate);

        return () => {
            cancelAnimationFrame(animFrameRef.current);
            group.clearLayers();
            group.remove();
        };
    }, [floodMode, routes, map]);

    return null;
}

// ─── Custom shelter DivIcon ─────────────────────────────────────────────────
function makeShelterIcon(state: 'target' | 'alt' | 'default') {
    const bg = state === 'target' ? '#16a34a' : state === 'alt' ? '#d97706' : '#0284c7';
    const size = state === 'target' ? 32 : 26;
    const half = size / 2;
    return L.divIcon({
        className: '',
        html: `<div style="width:${size}px;height:${size}px;background:${bg};border:3px solid white;border-radius:6px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,0.45);color:white;">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>`,
        iconAnchor: [half, half],
        popupAnchor: [0, -half],
    });
}

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
    const [floodSimMode, setFloodSimMode] = useState(false);
    const [sosActive, setSosActive] = useState(false);
    const [evacueeCount, setEvacueeCount] = useState(0);
    const [showAllRoutes, setShowAllRoutes] = useState(false);
    const [elapsed, setElapsed] = useState(0);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

    // Simulate live evacuee counter in SOS mode
    useEffect(() => {
        if (!sosActive) { setEvacueeCount(0); return; }
        const immediateRoutes = routes.filter(r => r.evacuation_urgency === 'immediate');
        const totalAtRisk = immediateRoutes.reduce((s, r) => s + Math.round(r.risk_level * 100), 0);
        if (timerRef.current) clearInterval(timerRef.current);
        timerRef.current = setInterval(() => {
            setEvacueeCount(prev => {
                const next = prev + Math.floor(Math.random() * 12 + 5);
                return next >= totalAtRisk ? totalAtRisk : next;
            });
            setElapsed(e => e + 1);
        }, 500);
        return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }, [sosActive, routes]);

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

    // Normalize route coords: API returns [lat, lon]; guard against [lon, lat] just in case
    const normalizeCoords = (rc: number[][]): [number, number][] =>
        rc.map(([a, b]) => (a > 10 && a < 25 ? [a, b] : [b, a]) as [number, number]);

    // Returns densified (Catmull-Rom) coords for smooth map rendering + animation
    const smoothCoords = (rc: number[][]): [number, number][] =>
        densifyCoords(normalizeCoords(rc), 40);

    const selectedCoords: [number, number][] = (() => {
        const rc = selectedRoute?.recommended_shelter?.route_coords;
        if (!rc || rc.length === 0) return [];
        return smoothCoords(rc);
    })();

    const PUNE_CENTER: [number, number] = [18.5204, 73.8567];
    const totalHighRisk = routes.filter(r => r.evacuation_urgency === 'immediate' || r.evacuation_urgency === 'prepare').length;
    const { t, lang } = useLang();

    const selectWard = useCallback((route: EvacRoute) => {
        setSelectedRoute(prev => prev?.ward_id === route.ward_id ? null : route);
    }, []);

    return (
        <div className="space-y-4">
            {/* SOS Banner */}
            {sosActive && (
                <div className="bg-red-600 text-white p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-4 border-red-800" style={{ animation: 'sos-flash 1s infinite' }}>
                    <div className="flex items-center gap-3">
                        <Radio className="w-5 h-5 sm:w-6 sm:h-6 shrink-0" />
                        <span className="font-black text-sm sm:text-lg">{t('emergencyBroadcast')}</span>
                        <span className="text-xs sm:text-sm opacity-90">{t('elapsed')}: {elapsed}s</span>
                    </div>
                    <div className="flex items-center gap-4 sm:gap-6">
                        <div className="text-center">
                            <div className="text-lg sm:text-2xl font-black">{evacueeCount.toLocaleString()}</div>
                            <div className="text-[10px] sm:text-xs opacity-80">{t('peopleEvacuating')}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg sm:text-2xl font-black">{totalHighRisk}</div>
                            <div className="text-[10px] sm:text-xs opacity-80">{t('highRiskWards')}</div>
                        </div>
                        <button onClick={() => { setSosActive(false); setElapsed(0); }} className="bg-white text-red-600 px-2 sm:px-3 py-1 font-black text-xs sm:text-sm">
                            {t('endBroadcast')}
                        </button>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="bg-white border-2 border-black p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                    <h2 className="text-lg sm:text-xl font-black flex items-center gap-2">
                        <Navigation className="w-5 h-5 sm:w-6 sm:h-6" />
                        {t('evacTitle')}
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-500">{t('evacSubtitle')}</p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    <button
                        onClick={() => setShowAllRoutes(v => !v)}
                        title="Toggle all ward routes on map"
                        className={`px-3 py-2 text-sm font-bold border-2 flex items-center gap-1 ${showAllRoutes ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:border-black'}`}
                    >
                        <Eye className="w-4 h-4" /> {t('allRoutes')}
                    </button>
                    <button
                        onClick={() => setFloodSimMode(v => !v)}
                        title="Animate flood spread from high-risk zones"
                        className={`px-3 py-2 text-sm font-bold border-2 flex items-center gap-1 ${floodSimMode ? 'bg-orange-500 text-white border-orange-500' : 'border-gray-300 hover:border-black'}`}
                    >
                        <Activity className="w-4 h-4" /> {t('floodSim')}
                    </button>
                    <button
                        onClick={() => { setSosActive(v => !v); if (sosActive) setElapsed(0); }}
                        className={`px-3 py-2 text-sm font-bold border-2 flex items-center gap-1 ${sosActive ? 'bg-red-600 text-white border-red-600' : 'border-red-600 text-red-600 hover:bg-red-600 hover:text-white'}`}
                    >
                        <Radio className="w-4 h-4" /> {t('sos')}
                    </button>
                    <button onClick={fetchRoutes} className="bg-black text-white px-4 py-2 font-bold text-sm flex items-center gap-1">
                        {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                        {loading ? '...' : t('computeRoutes')}
                    </button>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {[
                    { label: t('totalWards'), value: routes.length, icon: <MapPin className="w-4 h-4" />, color: 'border-black' },
                    { label: t('shelters'), value: shelters.length, icon: <Shield className="w-4 h-4 text-blue-600" />, color: 'border-blue-500' },
                    { label: t('immediate'), value: routes.filter(r => r.evacuation_urgency === 'immediate').length, icon: <AlertTriangle className="w-4 h-4 text-red-600" />, color: 'border-red-500' },
                    {
                        label: t('avgWalk'),
                        value: `${Math.round(routes.filter(r => r.recommended_shelter).reduce((s, r) => s + (r.recommended_shelter?.travel_time_min ?? 0), 0) / Math.max(routes.filter(r => r.recommended_shelter).length, 1))}m`,
                        icon: <Clock className="w-4 h-4 text-green-600" />,
                        color: 'border-green-500',
                    },
                ].map(stat => (
                    <div key={stat.label} className={`bg-white border-2 ${stat.color} p-3 flex items-center gap-3`}>
                        {stat.icon}
                        <div>
                            <div className="text-xl font-black">{stat.value}</div>
                            <div className="text-xs text-gray-500 uppercase font-bold">{stat.label}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-1">
                {['all', 'immediate', 'prepare', 'monitor', 'standby'].map(u => (
                    <button
                        key={u}
                        onClick={() => setFilterUrgency(u)}
                        className={`px-3 py-1 text-sm font-bold border-2 transition-all ${filterUrgency === u ? 'bg-black text-white border-black' : 'border-gray-300 hover:border-black'}`}
                    >
                        {u === 'all' ? t('allFilter') : t(urgencyKey(u))} ({u === 'all' ? routes.length : routes.filter(r => r.evacuation_urgency === u).length})
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                {/* Route List */}
                <div className="lg:col-span-3 bg-white border-2 border-black overflow-hidden flex flex-col h-[300px] lg:h-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
                    <div className="p-3 bg-black text-white font-black text-sm uppercase flex items-center gap-2">
                        <Navigation className="w-4 h-4" /> {t('wardRoutes')} ({filtered.length})
                    </div>
                    <div className="overflow-auto flex-1">
                        {filtered.map(route => (
                            <div
                                key={route.ward_id}
                                onClick={() => selectWard(route)}
                                className={`p-3 border-b-2 cursor-pointer hover:bg-gray-50 transition-colors ${selectedRoute?.ward_id === route.ward_id ? 'bg-gray-100 border-l-4 border-l-black' : ''}`}
                            >
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-sm">{wardName(route, lang)}</span>
                                    <span className={`text-xs px-2 py-0.5 font-bold ${getUrgencyStyle(route.evacuation_urgency)}`}>
                                        {t(urgencyKey(route.evacuation_urgency))}
                                    </span>
                                </div>
                                {route.recommended_shelter && (
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-1 text-xs text-gray-600">
                                            <MapPin className="w-3 h-3" />{route.recommended_shelter.shelter.name}
                                        </div>
                                        <div className="flex items-center gap-3 text-xs text-gray-500">
                                            <span className="flex items-center gap-0.5"><Navigation className="w-3 h-3" />{route.recommended_shelter.distance_km}km</span>
                                            <span className="flex items-center gap-0.5"><Clock className="w-3 h-3" />{route.recommended_shelter.travel_time_min}min</span>
                                            <span className={`flex items-center gap-0.5 ${getSafetyStyle(route.recommended_shelter.route_safety.status)}`}>
                                                <Shield className="w-3 h-3" />{t(safetyStatusKey(route.recommended_shelter.route_safety.status))}
                                            </span>
                                        </div>
                                    </div>
                                )}
                                <div className="mt-1 w-full bg-gray-200 h-1">
                                    <div className="h-1" style={{ width: `${route.risk_level}%`, backgroundColor: getRiskColor(route.risk_level) }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* MAP */}
                <div className="lg:col-span-5 border-2 border-black overflow-hidden relative h-[350px] sm:h-[400px] lg:h-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
                    {/* Map Legend */}
                    <div className="absolute top-2 left-2 z-[1000] bg-white border border-gray-300 text-xs p-2 space-y-1 shadow-lg rounded">
                        <div className="font-black text-xs uppercase mb-1">{t('legend')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500" /> {t('highRiskWard')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-yellow-500" /> {t('mediumRisk')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-green-500" /> {t('lowRisk')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-green-600" /> {t('recShelter')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-amber-600" /> {t('altShelter')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-blue-600" /> {t('otherShelter')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-6 border-t-[3px] border-green-600" /> {t('activeRoute')}</div>
                        <div className="flex items-center gap-1.5"><div className="w-6 border-t-2 border-dashed border-gray-400" /> {t('otherRoutes')}</div>
                    </div>

                    <MapContainer center={PUNE_CENTER} zoom={12} style={{ height: '100%', width: '100%' }} zoomControl={false}>
                        <TileLayer
                            attribution='&copy; <a href="https://carto.com">CARTO</a>'
                            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        />

                        <PulsingRiskOverlay routes={routes} floodMode={floodSimMode} />

                        {/* All routes toggle */}
                        {showAllRoutes && routes.map(route => {
                            if (!route.recommended_shelter?.route_coords) return null;
                            const coords = smoothCoords(route.recommended_shelter.route_coords);
                            return (
                                <Polyline
                                    key={`all-${route.ward_id}`}
                                    positions={coords}
                                    pathOptions={{ color: getRiskColor(route.risk_level), weight: 2.5, opacity: 0.5, dashArray: '6 4' }}
                                />
                            );
                        })}

                        {/* Selected route - animated */}
                        {selectedCoords.length > 1 && (
                            <>
                                {/* Shadow/glow */}
                                <Polyline positions={selectedCoords} pathOptions={{ color: '#16a34a', weight: 9, opacity: 0.25 }} />
                                {/* Main route */}
                                <Polyline positions={selectedCoords} pathOptions={{ color: '#16a34a', weight: 5, opacity: 0.95 }} />
                                {/* Dashed overlay for road look */}
                                <Polyline positions={selectedCoords} pathOptions={{ color: 'white', weight: 2, opacity: 0.6, dashArray: '12 8' }} />
                                <AnimatedRouteDot coords={selectedCoords} durationMs={6000} />
                            </>
                        )}

                        {/* Ward circle markers */}
                        {routes.map(route => (
                            <CircleMarker
                                key={route.ward_id}
                                center={[route.ward_centroid.lat, route.ward_centroid.lon]}
                                radius={selectedRoute?.ward_id === route.ward_id ? 14 : 9}
                                pathOptions={{
                                    color: selectedRoute?.ward_id === route.ward_id ? '#000' : getRiskColor(route.risk_level),
                                    fillColor: getRiskColor(route.risk_level),
                                    fillOpacity: 0.85,
                                    weight: selectedRoute?.ward_id === route.ward_id ? 3 : 1.5,
                                }}
                                eventHandlers={{ click: () => selectWard(route) }}
                            >
                                <Tooltip direction="top" offset={[0, -10]} opacity={1}>
                                    <b>{wardName(route, lang)}</b><br />
                                    {t('riskLabel')}: {route.risk_level}% &nbsp; <span style={{ textTransform: 'capitalize' }}>{t(urgencyKey(route.evacuation_urgency))}</span>
                                </Tooltip>
                                <Popup>
                                    <b>{wardName(route, lang)}</b><br />
                                    {t('riskLabel')}: {route.risk_level}%<br />
                                    {route.recommended_shelter && (
                                        <>{t('shelterLabel')}: {route.recommended_shelter.shelter.name}<br />
                                        {t('walkLabel')}: {route.recommended_shelter.travel_time_min} min</>
                                    )}
                                </Popup>
                            </CircleMarker>
                        ))}

                        {/* Shelter markers */}
                        {shelters.map(s => {
                            if (!s.lat || !s.lon) return null;
                            const isTarget = selectedRoute?.recommended_shelter?.shelter.id === s.id;
                            const isAlt = selectedRoute?.alternatives?.some(a => a?.shelter.id === s.id) ?? false;
                            const state: 'target' | 'alt' | 'default' = isTarget ? 'target' : isAlt ? 'alt' : 'default';
                            return (
                                <Marker
                                    key={s.id}
                                    position={[s.lat, s.lon]}
                                    icon={makeShelterIcon(state)}
                                    zIndexOffset={isTarget ? 2000 : isAlt ? 1000 : 0}
                                >
                                    <Tooltip direction="top" offset={[0, -14]} opacity={1}>
                                        <b>{s.name}</b><br />
                                        {t('capacity')}: {s.capacity}<br />
                                        <span style={{ textTransform: 'capitalize' }}>{s.type?.replace('_', ' ')}</span>
                                    </Tooltip>
                                    <Popup>
                                        <b>{s.name}</b><br />
                                        {t('capacity')}: {s.capacity}<br />
                                        {t('type')}: {s.type?.replace('_', ' ')}<br />
                                        {t('facilitiesLabel')}: {s.facilities?.join(', ')}
                                    </Popup>
                                </Marker>
                            );
                        })}
                    </MapContainer>
                </div>

                {/* Detail Panel */}
                <div className="lg:col-span-4 space-y-3 overflow-auto h-[400px] lg:h-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
                    {selectedRoute ? (
                        <>
                            {/* Ward header */}
                            <div className="bg-white border-2 border-black p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-xl font-black">{wardName(selectedRoute, lang)}</h3>
                                        <div className="text-sm text-gray-500">
                                            {t('riskLevel')}: <span className="font-bold" style={{ color: getRiskColor(selectedRoute.risk_level) }}>{selectedRoute.risk_level}%</span>
                                        </div>
                                    </div>
                                    <div className={`px-3 py-2 font-black flex items-center gap-1.5 text-sm ${getUrgencyStyle(selectedRoute.evacuation_urgency)}`}>
                                        {(selectedRoute.evacuation_urgency === 'immediate' || selectedRoute.evacuation_urgency === 'prepare') && <AlertTriangle className="w-4 h-4" />}
                                        {selectedRoute.evacuation_urgency === 'monitor' && <Eye className="w-4 h-4" />}
                                        {selectedRoute.evacuation_urgency === 'standby' && <Shield className="w-4 h-4" />}
                                        {selectedRoute.evacuation_urgency === 'immediate' ? t('evacuateNow') :
                                            selectedRoute.evacuation_urgency === 'prepare' ? t('prepare') :
                                                selectedRoute.evacuation_urgency === 'monitor' ? t('monitor') : t('standby')}
                                    </div>
                                </div>

                                {/* Walking ETA bar */}
                                {selectedRoute.recommended_shelter && (
                                    <div className="mt-3 bg-gray-50 p-2 border border-gray-200">
                                        <div className="flex items-center justify-between text-xs mb-1">
                                            <span className="font-bold flex items-center gap-1"><PersonStanding className="w-3 h-3" /> {t('walkingEta')}</span>
                                            <span className="font-black text-blue-600">{selectedRoute.recommended_shelter.travel_time_min} min</span>
                                        </div>
                                        <div className="w-full bg-gray-200 h-2">
                                            <div
                                                className="h-2 bg-blue-500 transition-all duration-700"
                                                style={{ width: `${Math.min((selectedRoute.recommended_shelter.travel_time_min / 120) * 100, 100)}%` }}
                                            />
                                        </div>
                                        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                                            <span>0</span><span>60min</span><span>120min</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Recommended Shelter */}
                            {selectedRoute.recommended_shelter && (
                                <div className="bg-green-50 border-2 border-green-500 p-4">
                                    <div className="flex items-center gap-2 mb-3">
                                        <Shield className="w-5 h-5 text-green-600" />
                                        <h4 className="font-black text-sm uppercase">{t('recommendedShelter')}</h4>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <div className="text-base font-black flex items-center gap-1">
                                                <MapPin className="w-4 h-4 text-green-700 flex-shrink-0" />
                                                {selectedRoute.recommended_shelter.shelter.name}
                                            </div>
                                            <div className="text-sm text-gray-600 mt-1">{t('type')}: {selectedRoute.recommended_shelter.shelter.type?.replace('_', ' ')}</div>
                                            <div className="flex items-center gap-2 mt-2 text-sm">
                                                <Users className="w-4 h-4" /> {t('capacity')}: <span className="font-bold">{selectedRoute.recommended_shelter.shelter.capacity}</span>
                                            </div>
                                            <div className="mt-2">
                                                <div className="text-xs text-gray-500 mb-0.5">{t('estimatedFillRate')}</div>
                                                <div className="w-full bg-gray-200 h-1.5">
                                                    <div className="h-1.5 bg-orange-500" style={{ width: `${Math.min(30 + selectedRoute.risk_level / 3, 92)}%` }} />
                                                </div>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2 text-sm">
                                                <Navigation className="w-4 h-4" /> {t('distance')}: <span className="font-bold">{selectedRoute.recommended_shelter.distance_km}km</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-sm">
                                                <Clock className="w-4 h-4" /> {t('walking')}: <span className="font-bold">{selectedRoute.recommended_shelter.travel_time_min} min</span>
                                            </div>
                                            <div className={`text-sm font-bold ${getSafetyStyle(selectedRoute.recommended_shelter.route_safety.status)}`}>
                                                {t('routeSafety')}: {Math.round(selectedRoute.recommended_shelter.route_safety.safety_score * 100)}%
                                                <span className="font-normal ml-1">({t(safetyStatusKey(selectedRoute.recommended_shelter.route_safety.status))})</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="mt-3 flex flex-wrap gap-1">
                                        {selectedRoute.recommended_shelter.shelter.facilities?.map(f => (
                                            <span key={f} className="bg-green-100 text-green-800 text-xs px-2 py-0.5 font-bold">{f}</span>
                                        ))}
                                    </div>
                                    {selectedRoute.recommended_shelter.route_safety.avoid_roads.length > 0 && (
                                        <div className="mt-3 bg-red-100 p-2 text-sm text-red-700 flex items-start gap-1">
                                            <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                            <span><span className="font-bold">{t('avoidFloodProne')}:</span> {selectedRoute.recommended_shelter.route_safety.avoid_roads.join(', ')}</span>
                                        </div>
                                    )}
                                    {(selectedRoute.recommended_shelter.route_safety.safe_alternatives ?? []).length > 0 && (
                                        <div className="mt-2 bg-green-100 p-2 text-sm text-green-700 flex items-start gap-1">
                                            <Navigation className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                            <span><span className="font-bold">{t('useInstead')}:</span> {(selectedRoute.recommended_shelter.route_safety.safe_alternatives ?? []).join(', ')}</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Alternative Shelters */}
                            {selectedRoute.alternatives && selectedRoute.alternatives.length > 0 && (
                                <div className="bg-white border-2 border-black overflow-hidden">
                                    <div className="p-3 bg-gray-800 text-white font-black text-sm uppercase flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4" /> {t('alternativeShelters')}
                                    </div>
                                    {selectedRoute.alternatives.map((alt, i) => alt && (
                                        <div key={i} className="p-3 border-b border-gray-200">
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <span className="font-bold text-sm flex items-center gap-1"><MapPin className="w-3 h-3" />{alt.shelter.name}</span>
                                                    <div className="text-xs text-gray-500">{alt.distance_km}km • {alt.travel_time_min}min {t('walkLabel')} • {t('capLabel')}: {alt.shelter.capacity}</div>
                                                </div>
                                                <span className={`text-xs font-bold ${getSafetyStyle(alt.route_safety.status)}`}>{t(safetyStatusKey(alt.route_safety.status))}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="bg-white border-2 border-black p-8 text-center text-gray-500 flex flex-col items-center gap-3">
                            <Navigation className="w-12 h-12 text-gray-300" />
                            <p className="font-bold">{t('clickWard')}</p>
                            <p className="text-xs text-gray-400">{t('routesAnimateRealtime')}</p>
                        </div>
                    )}

                    {/* All Shelters Grid */}
                    <div className="bg-white border-2 border-black overflow-hidden">
                        <div className="p-3 bg-black text-white font-black text-sm uppercase flex items-center gap-2">
                            <Shield className="w-4 h-4" /> {t('allShelters')} ({shelters.length})
                        </div>
                        <div className="grid grid-cols-2 gap-2 p-3 overflow-auto" style={{ maxHeight: 180 }}>
                            {shelters.map(s => (
                                <div key={s.id} className="border border-gray-200 p-2 text-xs hover:bg-gray-50">
                                    <div className="font-bold flex items-center gap-1"><Shield className="w-3 h-3 text-blue-600" />{s.name}</div>
                                    <div className="text-gray-500">{t('capLabel')}: {s.capacity} | {s.ward_id}</div>
                                    <div className="mt-1 w-full bg-gray-100 h-1">
                                        <div className="h-1 bg-blue-400" style={{ width: `${Math.min((s.capacity / 3000) * 100, 100)}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes pulse-dot { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.6);opacity:0.6} }
                @keyframes sos-flash { 0%,100%{opacity:1} 50%{opacity:0.85} }
            `}</style>
        </div>
    );
}

