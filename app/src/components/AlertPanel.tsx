import { useState, useEffect } from 'react';
import { Bell, MessageSquare, Phone, Shield, ChevronDown, ChevronUp, MapPin, Navigation, AlertTriangle, Send, CheckCircle, XCircle, Loader } from 'lucide-react';
import { API_BASE_URL, type Alert } from '@/lib/types';
import { useLang, wardName, priorityKey } from '@/lib/i18n';

interface Props {
    riskData: unknown[];
    wards: unknown[];
}

export default function AlertPanel(_props: Props) {
    const { t, lang } = useLang();
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [stats, setStats] = useState({ total: 0, emergency: 0, warning: 0, watch: 0, advisory: 0 });
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState<string>('all');
    const [expandedAlert, setExpandedAlert] = useState<string | null>(null);
    const [sendPhone, setSendPhone] = useState<Record<string, string>>({});
    const [sendState, setSendState] = useState<Record<string, 'idle' | 'sending' | 'ok' | 'err'>>({});
    const [sendError, setSendError] = useState<Record<string, string>>({});

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/alerts`);
            const data = await res.json();
            setAlerts(data.alerts || []);
            setStats({
                total: data.total_alerts || 0,
                ...data.by_priority,
            });
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAlerts(); }, []);

    const getPriorityStyle = (p: string) => {
        const styles: Record<string, string> = {
            emergency: 'border-red-500 bg-red-50',
            warning: 'border-orange-500 bg-orange-50',
            watch: 'border-yellow-500 bg-yellow-50',
            advisory: 'border-blue-500 bg-blue-50',
        };
        return styles[p] || 'border-gray-300 bg-white';
    };

    const getPriorityBadge = (p: string) => {
        const styles: Record<string, string> = {
            emergency: 'bg-red-600 text-white',
            warning: 'bg-orange-500 text-white',
            watch: 'bg-yellow-500 text-black',
            advisory: 'bg-blue-500 text-white',
        };
        return styles[p] || 'bg-gray-500 text-white';
    };

    const getChannelIcon = (ch: string) => {
        if (ch === 'sms') return <Phone className="w-4 h-4" />;
        if (ch === 'whatsapp') return <MessageSquare className="w-4 h-4" />;
        return <Bell className="w-4 h-4" />;
    };

    const filtered = filter === 'all' ? alerts : alerts.filter(a => a.priority === filter);
    const citizenAlerts = filtered.filter(a => a.alert_type === 'citizen');
    const authorityAlerts = filtered.filter(a => a.alert_type === 'authority');

    const sendAlert = async (alert: Alert, channel: 'sms' | 'whatsapp') => {
        const phone = sendPhone[alert.alert_id]?.trim();
        if (!phone) return;
        setSendState(s => ({ ...s, [alert.alert_id]: 'sending' }));
        setSendError(s => ({ ...s, [alert.alert_id]: '' }));
        try {
            // ── Build a clean, easy-to-read message ────────────────────
            const evac = alert.evacuation_route;
            const shelter = evac?.recommended_shelter;
            const riskPct = Math.round(alert.risk_score);
            const wName = alert.ward_name;

            let msg: string;
            if (lang === 'en') {
                msg = `⚠️ ${alert.hazard.toUpperCase()} ALERT — ${wName}\n`;
                msg += `Risk Level: ${riskPct}%\n\n`;
                if (shelter) {
                    msg += `🏠 Go to: ${shelter.name}\n`;
                    msg += `📏 Distance: ${shelter.distance_km} km (~${shelter.travel_time_min} min walk)\n`;
                    if (shelter.contact) msg += `📞 Contact: ${shelter.contact}\n`;
                    if (shelter.capacity) msg += `👥 Capacity: ${shelter.capacity} people\n`;
                    const avoid = evac?.route_safety?.avoid_roads;
                    if (avoid?.length) msg += `\n🚫 Avoid: ${avoid.join(', ')}\n`;
                }
                msg += `\n📌 Stay safe. Call 112 for emergency.`;
            } else {
                msg = `⚠️ ${alert.hazard === 'flood' ? 'पूर' : 'उष्णता'} सूचना — ${wName}\n`;
                msg += `धोका पातळी: ${riskPct}%\n\n`;
                if (shelter) {
                    msg += `🏠 येथे जा: ${shelter.name}\n`;
                    msg += `📏 अंतर: ${shelter.distance_km} किमी (~${shelter.travel_time_min} मिनिटे)\n`;
                    if (shelter.contact) msg += `📞 संपर्क: ${shelter.contact}\n`;
                }
                msg += `\n📌 सुरक्षित रहा. आपत्कालीन मदतीसाठी 112 वर कॉल करा.`;
            }

            // ── Extract map data ───────────────────────────────────────
            const routeCoords = evac?.route_coords;        // [[lat,lon], ...]
            const shelterCoords = shelter;
            const routeStart = routeCoords?.[0];
            const wardLat = routeStart?.[0] ?? (alert.shelter_info?.lat as number | undefined);
            const wardLon = routeStart?.[1] ?? (alert.shelter_info?.lon as number | undefined);

            const res = await fetch(`${API_BASE_URL}/api/alerts/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone,
                    channel,
                    title: lang === 'en' ? alert.title_en : alert.title_mr,
                    message: msg,
                    // Map coordinates + safe-route waypoints
                    ward_lat: wardLat,
                    ward_lon: wardLon,
                    shelter_lat: shelterCoords?.lat,
                    shelter_lon: shelterCoords?.lon,
                    ward_name: alert.ward_name,
                    shelter_name: shelterCoords?.name ?? '',
                    route_coords: routeCoords ?? [],
                }),
            });
            const data = await res.json();
            if (data.success) {
                setSendState(s => ({ ...s, [alert.alert_id]: 'ok' }));
                setTimeout(() => setSendState(s => ({ ...s, [alert.alert_id]: 'idle' })), 4000);
            } else {
                setSendState(s => ({ ...s, [alert.alert_id]: 'err' }));
                setSendError(s => ({ ...s, [alert.alert_id]: data.error || 'Send failed' }));
            }
        } catch {
            setSendState(s => ({ ...s, [alert.alert_id]: 'err' }));
            setSendError(s => ({ ...s, [alert.alert_id]: 'Network error' }));
        }
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="bg-white border-2 border-black p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                <div>
                    <h2 className="text-lg sm:text-xl font-black flex items-center gap-2">
                        <Bell className="w-5 h-5 sm:w-6 sm:h-6" />
                        {t('alertPanelTitle')}
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-500">{t('alertsSubtitle')}</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={fetchAlerts} className="bg-black text-white px-3 py-1 text-sm font-bold">
                        {loading ? '...' : t('generateAlerts')}
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {[
                    { key: 'all', label: t('alertTotal'), value: stats.total, color: 'border-black' },
                    { key: 'emergency', label: t('alertEmergency'), value: stats.emergency, color: 'border-red-500 text-red-600' },
                    { key: 'warning', label: t('alertWarning'), value: stats.warning, color: 'border-orange-500 text-orange-600' },
                    { key: 'watch', label: t('alertWatch'), value: stats.watch, color: 'border-yellow-500 text-yellow-600' },
                    { key: 'advisory', label: t('alertAdvisory'), value: stats.advisory, color: 'border-blue-500 text-blue-600' },
                ].map(s => (
                    <div
                        key={s.key}
                        onClick={() => setFilter(s.key)}
                        className={`bg-white border-2 p-3 text-center cursor-pointer transition-all hover:shadow-md ${s.color} ${filter === s.key ? 'shadow-lg ring-2 ring-black' : ''
                            }`}
                    >
                        <div className="text-xs font-bold uppercase">{s.label}</div>
                        <div className={`text-2xl font-black ${s.color}`}>{s.value}</div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Citizen Alerts */}
                <div>
                    <div className="bg-white border-2 border-black overflow-hidden">
                        <div className="p-3 bg-black text-white font-black text-sm uppercase flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" />
                            {t('citizenAlertsLabel')} ({citizenAlerts.length})
                        </div>
                        <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
                            {citizenAlerts.map(alert => (
                                <div key={alert.alert_id} className={`border-b-2 border-l-4 ${getPriorityStyle(alert.priority)}`}>
                                    <div
                                        className="p-3 cursor-pointer"
                                        onClick={() => setExpandedAlert(expandedAlert === alert.alert_id ? null : alert.alert_id)}
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-2">
                                                <span className={`text-xs px-2 py-0.5 font-bold ${getPriorityBadge(alert.priority)}`}>
                                                    {t(priorityKey(alert.priority))}
                                                </span>
                                                {getChannelIcon(alert.channel)}
                                                <span className="text-xs font-bold text-gray-500">{alert.channel === 'sms' ? t('channelSms') : t('channelWhatsapp')}</span>
                                            </div>
                                            {expandedAlert === alert.alert_id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                        </div>
                                        <h4 className="font-bold text-sm">
                                            {lang === 'en' ? alert.title_en : alert.title_mr}
                                        </h4>
                                    </div>
                                    {expandedAlert === alert.alert_id && (
                                        <div className="px-3 pb-3 space-y-2">
                                            {/* Message Preview */}
                                            <div className={`p-3 rounded-lg text-sm ${alert.channel === 'whatsapp' ? 'bg-green-100' : 'bg-gray-100'
                                                }`}>
                                                <div className="text-xs font-bold text-gray-500 mb-1">
                                                    {alert.channel === 'whatsapp' ? t('whatsappMsgLabel') : t('smsMsgLabel')}
                                                </div>
                                                <p className="whitespace-pre-line text-sm">
                                                    {lang === 'en' ? alert.message_en : alert.message_mr}
                                                </p>
                                            </div>
                                            {/* Actions */}
                                            <div>
                                                <div className="text-xs font-bold uppercase text-gray-500 mb-1">{t('recommendedActions')}</div>
                                                <ul className="text-xs space-y-1">
                                                    {alert.actions.map((a, i) => (
                                                        <li key={i} className="flex items-start gap-1">
                                                            <span className="text-green-500 mt-0.5">✓</span> {a}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                            {/* Shelter */}
                                            {alert.shelter_info && (
                                                <div className="bg-blue-50 p-2 text-xs">
                                                    <span className="font-bold">{t('nearestShelterLabel')}</span>{' '}
                                                    {String((alert.shelter_info as Record<string, unknown>).name || '')}
                                                    ({String((alert.shelter_info as Record<string, unknown>).distance_km || '')}km) —
                                                    {t('capacity')}: {String((alert.shelter_info as Record<string, unknown>).capacity || '')}
                                                </div>
                                            )}
                                            {/* Evacuation Route */}
                                            {alert.evacuation_route?.recommended_shelter && (
                                                <div className="border-2 border-black bg-yellow-50 p-2 space-y-1">
                                                    <div className="flex items-center gap-1 font-black text-xs uppercase">
                                                        <Navigation className="w-3 h-3" />
                                                        Evacuation Route
                                                    </div>
                                                    <div className="flex items-center gap-1 text-xs font-bold text-green-700">
                                                        <MapPin className="w-3 h-3" />
                                                        {alert.evacuation_route.recommended_shelter.name}
                                                        {' '}— {alert.evacuation_route.recommended_shelter.distance_km}km
                                                        (~{alert.evacuation_route.recommended_shelter.travel_time_min} min walk)
                                                    </div>
                                                    <div className="text-xs text-gray-600">
                                                        Facilities: {alert.evacuation_route.recommended_shelter.facilities.join(', ')}
                                                        {' '}· Capacity: {alert.evacuation_route.recommended_shelter.capacity}
                                                        {' '}· {alert.evacuation_route.recommended_shelter.contact}
                                                    </div>
                                                    {alert.evacuation_route.route_safety.avoid_roads.length > 0 && (
                                                        <div className="flex items-center gap-1 text-xs text-red-600 font-bold">
                                                            <AlertTriangle className="w-3 h-3" />
                                                            Avoid: {alert.evacuation_route.route_safety.avoid_roads.join(', ')}
                                                        </div>
                                                    )}
                                                    <div className={`text-xs font-bold ${
                                                        alert.evacuation_route.route_safety.status === 'safe' ? 'text-green-600'
                                                        : alert.evacuation_route.route_safety.status === 'moderate_risk' ? 'text-yellow-600'
                                                        : 'text-red-600'
                                                    }`}>
                                                        Route status: {alert.evacuation_route.route_safety.status.replace('_', ' ')}
                                                    </div>
                                                    {alert.evacuation_route.alternatives.length > 0 && (
                                                        <div className="text-xs text-gray-500">
                                                            Alt: {alert.evacuation_route.alternatives.map(a =>
                                                                `${a.name} (${a.distance_km}km)`
                                                            ).join(' · ')}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                            {/* ── Send via Twilio ── */}
                                            <div className="border-2 border-black p-2 bg-white space-y-1.5">
                                                <div className="flex items-center gap-1 text-xs font-black uppercase">
                                                    <Send className="w-3 h-3" />
                                                    Send to Phone
                                                </div>
                                                <div className="flex gap-1">
                                                    <input
                                                        type="tel"
                                                        placeholder="+91XXXXXXXXXX"
                                                        value={sendPhone[alert.alert_id] || ''}
                                                        onChange={e => setSendPhone(s => ({ ...s, [alert.alert_id]: e.target.value }))}
                                                        className="flex-1 border-2 border-black px-2 py-1 text-xs font-mono"
                                                    />
                                                    <button
                                                        onClick={() => sendAlert(alert, 'sms')}
                                                        disabled={sendState[alert.alert_id] === 'sending'}
                                                        className="bg-black text-white px-2 py-1 text-xs font-bold flex items-center gap-1 disabled:opacity-50"
                                                    >
                                                        {sendState[alert.alert_id] === 'sending' ? <Loader className="w-3 h-3 animate-spin" /> : <Phone className="w-3 h-3" />}
                                                        SMS
                                                    </button>
                                                    <button
                                                        onClick={() => sendAlert(alert, 'whatsapp')}
                                                        disabled={sendState[alert.alert_id] === 'sending'}
                                                        className="bg-green-600 text-white px-2 py-1 text-xs font-bold flex items-center gap-1 disabled:opacity-50"
                                                    >
                                                        {sendState[alert.alert_id] === 'sending' ? <Loader className="w-3 h-3 animate-spin" /> : <MessageSquare className="w-3 h-3" />}
                                                        WA
                                                    </button>
                                                </div>
                                                {sendState[alert.alert_id] === 'ok' && (
                                                    <div className="flex items-center gap-1 text-xs text-green-700 font-bold">
                                                        <CheckCircle className="w-3 h-3" /> Message sent successfully!
                                                    </div>
                                                )}
                                                {sendState[alert.alert_id] === 'err' && (
                                                    <div className="flex items-center gap-1 text-xs text-red-600 font-bold">
                                                        <XCircle className="w-3 h-3" /> {sendError[alert.alert_id]}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Authority Alerts */}
                <div>
                    <div className="bg-white border-2 border-black overflow-hidden">
                        <div className="p-3 bg-red-600 text-white font-black text-sm uppercase flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            {t('authorityAlertsLabel')} ({authorityAlerts.length})
                        </div>
                        <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
                            {authorityAlerts.length === 0 ? (
                                <div className="p-8 text-center text-gray-500 text-sm">
                                    {t('noAuthorityAlerts')}
                                </div>
                            ) : authorityAlerts.map(alert => (
                                <div key={alert.alert_id} className={`border-b-2 border-l-4 ${getPriorityStyle(alert.priority)} p-3`}>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs px-2 py-0.5 font-bold ${getPriorityBadge(alert.priority)}`}>
                                            {t(priorityKey(alert.priority))}
                                        </span>
                                        <span className="text-xs text-gray-500">{wardName(alert, lang)}</span>
                                    </div>
                                    <h4 className="font-bold text-sm mb-1">
                                        {lang === 'en' ? alert.title_en : alert.title_mr}
                                    </h4>
                                    <p className="text-xs text-gray-600 whitespace-pre-line">
                                        {lang === 'en' ? alert.message_en : alert.message_mr}
                                    </p>                                    {/* Evacuation Route for Authority */}
                                    {alert.evacuation_route?.recommended_shelter && (
                                        <div className="mt-2 border-l-4 border-yellow-500 pl-2 space-y-0.5">
                                            <div className="flex items-center gap-1 text-xs font-black uppercase">
                                                <Navigation className="w-3 h-3" />
                                                Evacuation Route
                                            </div>
                                            <div className="text-xs font-bold text-green-700">
                                                → {alert.evacuation_route.recommended_shelter.name}
                                                {' '}({alert.evacuation_route.recommended_shelter.distance_km}km,
                                                ~{alert.evacuation_route.recommended_shelter.travel_time_min} min)
                                                · Cap: {alert.evacuation_route.recommended_shelter.capacity}
                                                · {alert.evacuation_route.recommended_shelter.contact}
                                            </div>
                                            <div className="text-xs">Facilities: {alert.evacuation_route.recommended_shelter.facilities.join(', ')}</div>
                                            {alert.evacuation_route.route_safety.avoid_roads.length > 0 && (
                                                <div className="text-xs text-red-600 font-bold">
                                                    ⚠ Avoid: {alert.evacuation_route.route_safety.avoid_roads.join(', ')}
                                                </div>
                                            )}
                                            {alert.evacuation_route.alternatives.length > 0 && (
                                                <div className="text-xs text-gray-500">
                                                    Alt shelters: {alert.evacuation_route.alternatives.map(a => `${a.name} (${a.distance_km}km)`).join(' · ')}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {/* ── Send via Twilio ── */}
                                    <div className="mt-2 border-2 border-black p-2 bg-white space-y-1.5">
                                        <div className="flex items-center gap-1 text-xs font-black uppercase">
                                            <Send className="w-3 h-3" />
                                            Send to Phone
                                        </div>
                                        <div className="flex gap-1">
                                            <input
                                                type="tel"
                                                placeholder="+91XXXXXXXXXX"
                                                value={sendPhone[alert.alert_id] || ''}
                                                onChange={e => setSendPhone(s => ({ ...s, [alert.alert_id]: e.target.value }))}
                                                className="flex-1 border-2 border-black px-2 py-1 text-xs font-mono"
                                            />
                                            <button
                                                onClick={() => sendAlert(alert, 'sms')}
                                                disabled={sendState[alert.alert_id] === 'sending'}
                                                className="bg-black text-white px-2 py-1 text-xs font-bold flex items-center gap-1 disabled:opacity-50"
                                            >
                                                {sendState[alert.alert_id] === 'sending' ? <Loader className="w-3 h-3 animate-spin" /> : <Phone className="w-3 h-3" />}
                                                SMS
                                            </button>
                                            <button
                                                onClick={() => sendAlert(alert, 'whatsapp')}
                                                disabled={sendState[alert.alert_id] === 'sending'}
                                                className="bg-green-600 text-white px-2 py-1 text-xs font-bold flex items-center gap-1 disabled:opacity-50"
                                            >
                                                {sendState[alert.alert_id] === 'sending' ? <Loader className="w-3 h-3 animate-spin" /> : <MessageSquare className="w-3 h-3" />}
                                                WA
                                            </button>
                                        </div>
                                        {sendState[alert.alert_id] === 'ok' && (
                                            <div className="flex items-center gap-1 text-xs text-green-700 font-bold">
                                                <CheckCircle className="w-3 h-3" /> Message sent successfully!
                                            </div>
                                        )}
                                        {sendState[alert.alert_id] === 'err' && (
                                            <div className="flex items-center gap-1 text-xs text-red-600 font-bold">
                                                <XCircle className="w-3 h-3" /> {sendError[alert.alert_id]}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
