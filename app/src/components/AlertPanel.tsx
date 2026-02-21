import { useState, useEffect } from 'react';
import { Bell, MessageSquare, Phone, Shield, ChevronDown, ChevronUp } from 'lucide-react';
import { API_BASE_URL, type Alert } from '@/lib/types';

interface Props {
    riskData: unknown[];
    wards: unknown[];
}

export default function AlertPanel(_props: Props) {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [stats, setStats] = useState({ total: 0, emergency: 0, warning: 0, watch: 0, advisory: 0 });
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState<string>('all');
    const [language, setLanguage] = useState<'en' | 'mr'>('en');
    const [expandedAlert, setExpandedAlert] = useState<string | null>(null);

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

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="bg-white border-2 border-black p-4 flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-black flex items-center gap-2">
                        <Bell className="w-6 h-6" />
                        Alert System — SMS / WhatsApp Integration
                    </h2>
                    <p className="text-sm text-gray-500">Real-time bilingual alerts for citizens and authorities</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setLanguage(language === 'en' ? 'mr' : 'en')}
                        className="border-2 border-black px-3 py-1 text-sm font-bold hover:bg-black hover:text-white"
                    >
                        {language === 'en' ? '🇮🇳 Marathi' : '🇬🇧 English'}
                    </button>
                    <button onClick={fetchAlerts} className="bg-black text-white px-3 py-1 text-sm font-bold">
                        {loading ? '...' : 'Generate Alerts'}
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-5 gap-3">
                {[
                    { key: 'all', label: 'Total', value: stats.total, color: 'border-black' },
                    { key: 'emergency', label: 'Emergency', value: stats.emergency, color: 'border-red-500 text-red-600' },
                    { key: 'warning', label: 'Warning', value: stats.warning, color: 'border-orange-500 text-orange-600' },
                    { key: 'watch', label: 'Watch', value: stats.watch, color: 'border-yellow-500 text-yellow-600' },
                    { key: 'advisory', label: 'Advisory', value: stats.advisory, color: 'border-blue-500 text-blue-600' },
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

            <div className="grid grid-cols-2 gap-4">
                {/* Citizen Alerts */}
                <div>
                    <div className="bg-white border-2 border-black overflow-hidden">
                        <div className="p-3 bg-black text-white font-black text-sm uppercase flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" />
                            Citizen Alerts ({citizenAlerts.length})
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
                                                    {alert.priority.toUpperCase()}
                                                </span>
                                                {getChannelIcon(alert.channel)}
                                                <span className="text-xs font-bold text-gray-500">{alert.channel.toUpperCase()}</span>
                                            </div>
                                            {expandedAlert === alert.alert_id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                        </div>
                                        <h4 className="font-bold text-sm">
                                            {language === 'en' ? alert.title_en : alert.title_mr}
                                        </h4>
                                    </div>
                                    {expandedAlert === alert.alert_id && (
                                        <div className="px-3 pb-3 space-y-2">
                                            {/* Message Preview */}
                                            <div className={`p-3 rounded-lg text-sm ${alert.channel === 'whatsapp' ? 'bg-green-100' : 'bg-gray-100'
                                                }`}>
                                                <div className="text-xs font-bold text-gray-500 mb-1">
                                                    {alert.channel === 'whatsapp' ? '💬 WhatsApp Message' : '📱 SMS Message'}
                                                </div>
                                                <p className="whitespace-pre-line text-sm">
                                                    {language === 'en' ? alert.message_en : alert.message_mr}
                                                </p>
                                            </div>
                                            {/* Actions */}
                                            <div>
                                                <div className="text-xs font-bold uppercase text-gray-500 mb-1">Recommended Actions:</div>
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
                                                    <span className="font-bold">🏛️ Nearest Shelter:</span>{' '}
                                                    {String((alert.shelter_info as Record<string, unknown>).name || '')}
                                                    ({String((alert.shelter_info as Record<string, unknown>).distance_km || '')}km) —
                                                    Capacity: {String((alert.shelter_info as Record<string, unknown>).capacity || '')}
                                                </div>
                                            )}
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
                            Authority / PMC Alerts ({authorityAlerts.length})
                        </div>
                        <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
                            {authorityAlerts.length === 0 ? (
                                <div className="p-8 text-center text-gray-500 text-sm">
                                    No authority-level alerts at current risk levels
                                </div>
                            ) : authorityAlerts.map(alert => (
                                <div key={alert.alert_id} className={`border-b-2 border-l-4 ${getPriorityStyle(alert.priority)} p-3`}>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs px-2 py-0.5 font-bold ${getPriorityBadge(alert.priority)}`}>
                                            {alert.priority.toUpperCase()}
                                        </span>
                                        <span className="text-xs text-gray-500">{alert.ward_name}</span>
                                    </div>
                                    <h4 className="font-bold text-sm mb-1">
                                        {language === 'en' ? alert.title_en : alert.title_mr}
                                    </h4>
                                    <p className="text-xs text-gray-600 whitespace-pre-line">
                                        {language === 'en' ? alert.message_en : alert.message_mr}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
