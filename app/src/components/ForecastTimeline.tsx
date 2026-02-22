import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Clock, TrendingUp, TrendingDown, AlertTriangle, CloudRain, Thermometer } from 'lucide-react';
import { API_BASE_URL, getRiskColor, type WardForecast, type ForecastTimepoint } from '@/lib/types';
import { useLang, wardName, trendKey, priorityKey } from '@/lib/i18n';

interface Props {
    riskData: unknown[];
    wards: unknown[];
}

export default function ForecastTimeline(_props: Props) {
    const { t, lang } = useLang();
    const [forecasts, setForecasts] = useState<WardForecast[]>([]);
    const [selectedWard, setSelectedWard] = useState<WardForecast | null>(null);
    const [loading, setLoading] = useState(false);
    const [dangerWindow, setDangerWindow] = useState<{ start_hour: number; end_hour: number } | null>(null);
    const [stats, setStats] = useState({ total: 0, critical: 0, rising: 0 });

    const fetchForecast = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/forecast`);
            const data = await res.json();
            setForecasts(data.forecasts || []);
            setDangerWindow(data.danger_window || null);
            setStats({
                total: data.total_wards || 0,
                critical: data.wards_reaching_critical || 0,
                rising: data.wards_risk_rising || 0,
            });
            if (data.forecasts?.length > 0 && !selectedWard) {
                setSelectedWard(data.forecasts[0]);
            }
        } catch (err) {
            console.error('Failed to fetch forecasts:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchForecast(); }, []);

    const getAlertBadge = (level: string) => {
        const styles: Record<string, string> = {
            emergency: 'bg-red-600 text-white',
            warning: 'bg-orange-500 text-white',
            watch: 'bg-yellow-500 text-black',
            advisory: 'bg-blue-500 text-white',
            normal: 'bg-green-500 text-white',
        };
        return styles[level] || styles.normal;
    };

    const getTrendIcon = (trend: string) => {
        if (trend === 'rising') return <TrendingUp className="w-4 h-4 text-red-500" />;
        if (trend === 'falling') return <TrendingDown className="w-4 h-4 text-green-500" />;
        return <span className="text-gray-400">→</span>;
    };

    return (
        <div className="space-y-4">
            {/* Header Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                <div className="bg-white border-2 border-black p-4">
                    <div className="text-xs font-bold uppercase text-gray-500">{t('totalWardsLabel')}</div>
                    <div className="text-3xl font-black">{stats.total}</div>
                </div>
                <div className="bg-white border-2 border-red-500 p-4">
                    <div className="text-xs font-bold uppercase text-red-500">{t('reachingCritical')}</div>
                    <div className="text-3xl font-black text-red-600">{stats.critical}</div>
                </div>
                <div className="bg-white border-2 border-orange-500 p-4">
                    <div className="text-xs font-bold uppercase text-orange-500">{t('riskRising')}</div>
                    <div className="text-3xl font-black text-orange-600">{stats.rising}</div>
                </div>
                <div className={`border-2 p-4 ${dangerWindow ? 'bg-red-50 border-red-500' : 'bg-green-50 border-green-500'}`}>
                    <div className="text-xs font-bold uppercase">{t('dangerWindow')}</div>
                    <div className="text-sm font-black">
                        {dangerWindow
                            ? `T+${dangerWindow.start_hour}h → T+${dangerWindow.end_hour}h`
                            : t('noneDetected')
                        }
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                {/* Ward Forecast List */}
                <div className="lg:col-span-4 bg-white border-2 border-black overflow-hidden" style={{ maxHeight: 'calc(100vh - 340px)' }}>
                    <div className="p-3 bg-black text-white flex items-center justify-between">
                        <h2 className="font-black uppercase tracking-wider text-sm">
                            <Clock className="w-4 h-4 inline mr-2" />
                            {t('forecastListTitle')}
                        </h2>
                        <button onClick={fetchForecast} className="text-xs border border-white px-2 py-1 hover:bg-white hover:text-black">
                            {loading ? '...' : t('refresh')}
                        </button>
                    </div>
                    <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 400px)' }}>
                        {forecasts.map(fc => (
                            <div
                                key={fc.ward_id}
                                onClick={() => setSelectedWard(fc)}
                                className={`p-3 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors ${selectedWard?.ward_id === fc.ward_id ? 'bg-gray-100 border-l-4 border-l-black' : ''
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-sm">{wardName(fc, lang)}</span>
                                    <span className={`text-xs px-2 py-0.5 font-bold ${getAlertBadge(fc.max_alert)}`}>
                                        {t(priorityKey(fc.max_alert))}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span className="flex items-center gap-1">
                                        {t('peakAtLabel')} <span className="font-bold" style={{ color: getRiskColor(fc.peak.risk) }}>{fc.peak.risk}%</span> {t('atLabel')} T+{fc.peak.hour}h
                                    </span>
                                    <span className="flex items-center gap-1">
                                        {getTrendIcon(fc.trend)} {t(trendKey(fc.trend))}
                                    </span>
                                </div>
                                {fc.time_to_critical !== null && (
                                    <div className="text-xs text-red-600 font-bold mt-1">
                                        ⚠ {t('criticalInHours')} {fc.time_to_critical}h
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Chart + Details */}
                <div className="lg:col-span-8 space-y-4">
                    {selectedWard ? (
                        <>
                            {/* Ward Header */}
                            <div className="bg-white border-2 border-black p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-xl font-black">{wardName(selectedWard, lang)}</h3>
                                        <div className="text-sm text-gray-500">
                                            {t('populationStat')}: {selectedWard.population?.toLocaleString()} |
                                            {t('baselineFloodStat')}: {selectedWard.baseline.flood}% |
                                            {t('baselineHeatStat')}: {selectedWard.baseline.heat}%
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-gray-500">{t('peakRisk')}</div>
                                        <div className="text-3xl font-black" style={{ color: getRiskColor(selectedWard.peak.risk) }}>
                                            {selectedWard.peak.risk}%
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {selectedWard.peak.hazard === 'flood' ? <CloudRain className="w-3 h-3 inline" /> : <Thermometer className="w-3 h-3 inline" />}
                                            {' '}{t('atLabel')} T+{selectedWard.peak.hour}h
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Timeline Chart */}
                            <div className="bg-white border-2 border-black p-4" style={{ height: 350 }}>
                                <h4 className="font-black text-sm uppercase mb-2">{t('riskTimeline')}</h4>
                                <ResponsiveContainer width="100%" height="90%">
                                    <AreaChart data={selectedWard.timeline}>
                                        <defs>
                                            <linearGradient id="floodGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="heatGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="hour" tickFormatter={(h: number) => `T+${h}h`} />
                                        <YAxis domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
                                        <Tooltip
                                            formatter={(value: number, name: string) => [`${value}%`, name]}
                                            labelFormatter={(h: number) => `T+${h} hours`}
                                        />
                                        <ReferenceLine y={75} stroke="#ef4444" strokeDasharray="5 5" label={t('criticalLine')} />
                                        <ReferenceLine y={60} stroke="#f97316" strokeDasharray="5 5" label={t('highLine')} />
                                        <Area type="monotone" dataKey="flood_risk" stroke="#3b82f6" fill="url(#floodGrad)" name={t('floodRiskName')} strokeWidth={2} />
                                        <Area type="monotone" dataKey="heat_risk" stroke="#ef4444" fill="url(#heatGrad)" name={t('heatRiskName')} strokeWidth={2} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Hourly Breakdown */}
                            <div className="bg-white border-2 border-black p-4 overflow-x-auto">
                                <h4 className="font-black text-sm uppercase mb-2">{t('hourlyDetail')}</h4>
                                <div className="flex gap-2">
                                    {selectedWard.timeline.map((tp: ForecastTimepoint) => (
                                        <div key={tp.hour} className="flex-shrink-0 text-center p-2 border border-gray-200 min-w-[80px]"
                                            style={{ backgroundColor: `${getRiskColor(tp.combined_risk)}15` }}>
                                            <div className="text-xs font-bold text-gray-500">T+{tp.hour}h</div>
                                            <div className="text-lg font-black" style={{ color: getRiskColor(tp.combined_risk) }}>
                                                {tp.combined_risk}%
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                <CloudRain className="w-3 h-3 inline" /> {tp.rainfall_mm}mm
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                <Thermometer className="w-3 h-3 inline" /> {tp.temperature_c}°C
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="bg-white border-2 border-black p-8 text-center text-gray-500">
                            <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p className="font-bold">{t('selectWardForecast')}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
