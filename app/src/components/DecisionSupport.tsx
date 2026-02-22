import { useState, useEffect } from 'react';
import { Target, AlertCircle, Clock, CheckCircle, ArrowRight, Zap, ShieldCheck, Eye } from 'lucide-react';
import { API_BASE_URL, type ActionItem } from '@/lib/types';
import { useLang, wardName, categoryKey, resourceKey } from '@/lib/i18n';

interface Props {
    riskData: unknown[];
    wards: unknown[];
}

interface KPIs {
    critical_actions_pending: number;
    total_actions: number;
    critical_wards: number;
    population_at_risk: number;
    response_readiness: string;
    deployed: number;
    resolved: number;
}

export default function DecisionSupport(_props: Props) {
    const { t, lang } = useLang();
    const [actions, setActions] = useState<ActionItem[]>([]);
    const [kpis, setKpis] = useState<KPIs | null>(null);
    const [situationLevel, setSituationLevel] = useState('GREEN');
    const [stats, setStats] = useState({ immediate: 0, next_6h: 0, next_24h: 0, advisory: 0 });
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState<string>('all');
    const [acknowledgedIds, setAcknowledgedIds] = useState<Set<string>>(new Set());

    const fetchPlan = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/decision-support`);
            const data = await res.json();
            setActions(data.actions || []);
            setKpis(data.kpis || null);
            setSituationLevel(data.situation_level || 'GREEN');
            setStats(data.by_priority || { immediate: 0, next_6h: 0, next_24h: 0, advisory: 0 });
        } catch (err) {
            console.error('Failed to fetch decision support:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchPlan(); }, []);

    const acknowledge = (id: string) => {
        setAcknowledgedIds(prev => new Set([...prev, id]));
    };

    const getSituationStyle = (level: string) => {
        const styles: Record<string, string> = {
            RED: 'bg-red-600 text-white animate-pulse',
            ORANGE: 'bg-orange-500 text-white',
            YELLOW: 'bg-yellow-400 text-black',
            GREEN: 'bg-green-500 text-white',
        };
        return styles[level] || styles.GREEN;
    };

    const getPriorityStyle = (p: string) => {
        const styles: Record<string, { border: string; bg: string; badge: string; icon: React.ReactNode }> = {
            immediate: {
                border: 'border-red-500',
                bg: 'bg-red-50',
                badge: 'bg-red-600 text-white',
                icon: <Zap className="w-5 h-5 text-red-600" />,
            },
            next_6h: {
                border: 'border-orange-500',
                bg: 'bg-orange-50',
                badge: 'bg-orange-500 text-white',
                icon: <Clock className="w-5 h-5 text-orange-500" />,
            },
            next_24h: {
                border: 'border-yellow-500',
                bg: 'bg-yellow-50',
                badge: 'bg-yellow-500 text-black',
                icon: <Target className="w-5 h-5 text-yellow-600" />,
            },
            advisory: {
                border: 'border-blue-500',
                bg: 'bg-blue-50',
                badge: 'bg-blue-500 text-white',
                icon: <Eye className="w-5 h-5 text-blue-500" />,
            },
        };
        return styles[p] || styles.advisory;
    };

    const getCategoryIcon = (c: string) => {
        const icons: Record<string, string> = {
            deploy: '🚛',
            evacuate: '🚨',
            alert: '📢',
            monitor: '👁️',
            prepare: '📦',
        };
        return icons[c] || '📋';
    };

    const filtered = filter === 'all' ? actions : actions.filter(a => a.priority === filter);

    return (
        <div className="space-y-4">
            {/* Situation Level Header */}
            <div className={`border-2 border-black p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 ${getSituationStyle(situationLevel)}`}>
                <div className="flex items-center gap-3 sm:gap-4">
                    <div className="text-3xl sm:text-4xl font-black">🎯</div>
                    <div>
                        <h2 className="text-xl sm:text-2xl font-black tracking-tight">{t('commandCenter')}</h2>
                        <p className="text-xs sm:text-sm opacity-80">{t('decisionSupportSubtitle')}</p>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-xs font-bold uppercase opacity-70">{t('situationLevel')}</div>
                    <div className="text-3xl font-black">{situationLevel}</div>
                </div>
            </div>

            {/* KPI Strip */}
            {kpis && (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    <div className="bg-red-50 border-2 border-red-500 p-3 text-center">
                        <div className="text-xs font-bold uppercase text-red-500">{t('criticalPending')}</div>
                        <div className="text-3xl font-black text-red-600">{kpis.critical_actions_pending}</div>
                    </div>
                    <div className="bg-white border-2 border-black p-3 text-center">
                        <div className="text-xs font-bold uppercase text-gray-500">{t('totalActions')}</div>
                        <div className="text-3xl font-black">{kpis.total_actions}</div>
                    </div>
                    <div className="bg-white border-2 border-orange-500 p-3 text-center">
                        <div className="text-xs font-bold uppercase text-orange-500">{t('criticalWards')}</div>
                        <div className="text-3xl font-black text-orange-600">{kpis.critical_wards}</div>
                    </div>
                    <div className="bg-white border-2 border-purple-500 p-3 text-center">
                        <div className="text-xs font-bold uppercase text-purple-500">{t('populationAtRisk')}</div>
                        <div className="text-xl font-black text-purple-600">{kpis.population_at_risk?.toLocaleString()}</div>
                    </div>
                    <div className="bg-green-50 border-2 border-green-500 p-3 text-center">
                        <div className="text-xs font-bold uppercase text-green-500">{t('deployed')}</div>
                        <div className="text-3xl font-black text-green-600">{acknowledgedIds.size}</div>
                    </div>
                    <div className={`p-3 text-center border-2 ${kpis.response_readiness === 'HIGH' ? 'bg-green-50 border-green-500' :
                        kpis.response_readiness === 'MODERATE' ? 'bg-yellow-50 border-yellow-500' :
                            'bg-red-50 border-red-500'
                        }`}>
                        <div className="text-xs font-bold uppercase">{t('readiness')}</div>
                        <div className="text-xl font-black">{kpis.response_readiness}</div>
                    </div>
                </div>
            )}

            {/* Filter Tabs */}
            <div className="flex gap-2">
                {[
                    { key: 'all', label: t('allFilter'), count: actions.length },
                    { key: 'immediate', label: `🔴 ${t('immediateFilter')}`, count: stats.immediate },
                    { key: 'next_6h', label: `🟠 ${t('next6hFilter')}`, count: stats.next_6h },
                    { key: 'next_24h', label: `🟡 ${t('next24hFilter')}`, count: stats.next_24h },
                    { key: 'advisory', label: `🔵 ${t('advisoryFilter')}`, count: stats.advisory },
                ].map(f => (
                    <button
                        key={f.key}
                        onClick={() => setFilter(f.key)}
                        className={`px-3 py-1 text-sm font-bold border-2 transition-all ${filter === f.key ? 'bg-black text-white border-black' : 'border-gray-300 hover:border-black'
                            }`}
                    >
                        {f.label} ({f.count})
                    </button>
                ))}
                <button
                    onClick={fetchPlan}
                    className="ml-auto bg-black text-white px-4 py-1 text-sm font-bold"
                >
                    {loading ? t('loadingLabel') : t('refreshPlan')}
                </button>
            </div>

            {/* Action Cards */}
            <div className="space-y-3">
                {filtered.map(action => {
                    const style = getPriorityStyle(action.priority);
                    const isAcknowledged = acknowledgedIds.has(action.action_id);

                    return (
                        <div
                            key={action.action_id}
                            className={`border-2 ${style.border} ${isAcknowledged ? 'opacity-60' : ''} ${style.bg} overflow-hidden`}
                        >
                            <div className="p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3 flex-1">
                                        <div className="mt-1">{style.icon}</div>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`text-xs px-2 py-0.5 font-bold ${style.badge}`}>
                                                    {action.priority === 'next_6h' ? t('next6hBadge') :
                                                        action.priority === 'next_24h' ? t('next24hBadge') :
                                                            action.priority === 'immediate' ? t('immediateFilter').toUpperCase() :
                                                                t('advisoryFilter').toUpperCase()}
                                                </span>
                                                <span className="text-xs bg-gray-200 px-2 py-0.5 font-bold">
                                                    {getCategoryIcon(action.category)} {t(categoryKey(action.category))}
                                                </span>
                                                <span className="text-xs text-gray-500">{wardName(action, lang)}</span>
                                            </div>
                                            <h4 className="font-black text-sm">{action.title}</h4>
                                            <p className="text-sm text-gray-600 mt-1">{action.description}</p>

                                            {/* Justification */}
                                            <div className="mt-2 bg-white bg-opacity-50 p-2 text-xs text-gray-600">
                                                <span className="font-bold">{t('why')} </span>{action.justification}
                                            </div>

                                            {/* Resources Needed */}
                                            {action.resources_needed.length > 0 && (
                                                <div className="mt-2 flex flex-wrap gap-2">
                                                    {action.resources_needed.map((r, i) => (
                                                        <span key={i} className="bg-white border border-gray-300 text-xs px-2 py-1 font-bold">
                                                            {r.count}× {t(resourceKey(r.type))}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Impact */}
                                            <div className="mt-2 text-xs text-gray-500">
                                                <AlertCircle className="w-3 h-3 inline mr-1" />
                                                <span className="font-bold">{t('impact')} </span>{action.estimated_impact}
                                            </div>

                                            {/* Assignment */}
                                            <div className="mt-1 text-xs text-gray-400">
                                                <ShieldCheck className="w-3 h-3 inline mr-1" />
                                                {t('assignedLabel')} {action.assigned_to}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="flex flex-col gap-1 ml-4">
                                        {!isAcknowledged ? (
                                            <button
                                                onClick={() => acknowledge(action.action_id)}
                                                className="bg-black text-white px-3 py-2 text-xs font-bold flex items-center gap-1 hover:bg-gray-800"
                                            >
                                                <CheckCircle className="w-3 h-3" /> {t('acknowledgeBtn')}
                                            </button>
                                        ) : (
                                            <div className="flex flex-col gap-1">
                                                <span className="bg-green-100 text-green-700 px-3 py-2 text-xs font-bold flex items-center gap-1">
                                                    <CheckCircle className="w-3 h-3" /> {t('acknowledgedLabel')}
                                                </span>
                                                <button className="bg-blue-600 text-white px-3 py-1 text-xs font-bold flex items-center gap-1">
                                                    <ArrowRight className="w-3 h-3" /> {t('deployBtn')}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {filtered.length === 0 && (
                    <div className="bg-white border-2 border-green-500 p-8 text-center text-green-600">
                        <CheckCircle className="w-12 h-12 mx-auto mb-3" />
                        <p className="font-black text-lg">{t('allClear')}</p>
                        <p className="text-sm text-gray-500">{t('noActionsRequired')}</p>
                    </div>
                )}
            </div>
        </div>
    );
}
