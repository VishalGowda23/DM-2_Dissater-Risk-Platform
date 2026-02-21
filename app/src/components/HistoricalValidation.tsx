import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { History, CheckCircle, XCircle, Clock } from 'lucide-react';
import { API_BASE_URL, getRiskColor, type HistoricalEvent, type WardPrediction } from '@/lib/types';

interface Props {
    riskData: unknown[];
    wards: unknown[];
}

export default function HistoricalValidation(_props: Props) {
    const [events, setEvents] = useState<HistoricalEvent[]>([]);
    const [selectedEvent, setSelectedEvent] = useState<string | null>(null);
    const [validation, setValidation] = useState<{
        validation: Record<string, number | boolean>;
        ward_predictions: WardPrediction[];
        event: HistoricalEvent;
    } | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetch(`${API_BASE_URL}/api/historical/events`)
            .then(res => res.json())
            .then(data => setEvents(data.events || []))
            .catch(console.error);
    }, []);

    const validateEvent = async (eventId: string) => {
        setSelectedEvent(eventId);
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/historical/validate/${eventId}`, {
                method: 'POST',
            });
            const data = await res.json();
            setValidation(data);
        } catch (err) {
            console.error('Validation failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const getSeverityColor = (s: string) => {
        if (s === 'catastrophic') return 'bg-red-600 text-white';
        if (s === 'severe') return 'bg-orange-500 text-white';
        return 'bg-yellow-500 text-black';
    };

    const getClassColor = (c: string) => {
        if (c === 'true_positive') return 'text-green-600';
        if (c === 'true_negative') return 'text-gray-400';
        if (c === 'false_positive') return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="bg-white border-2 border-black p-4">
                <h2 className="text-xl font-black flex items-center gap-2">
                    <History className="w-6 h-6" />
                    Historical Event Validation
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                    Validate our risk model against real documented Pune disaster events using actual archived weather data
                </p>
            </div>

            <div className="grid grid-cols-12 gap-4">
                {/* Event Cards */}
                <div className="col-span-4 space-y-3">
                    {events.map(event => (
                        <div
                            key={event.event_id}
                            onClick={() => validateEvent(event.event_id)}
                            className={`bg-white border-2 p-4 cursor-pointer transition-all hover:shadow-lg ${selectedEvent === event.event_id ? 'border-black shadow-lg' : 'border-gray-300'
                                }`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className={`text-xs font-bold px-2 py-0.5 ${getSeverityColor(event.severity)}`}>
                                    {event.severity.toUpperCase()}
                                </span>
                                <span className="text-xs text-gray-500">{event.date}</span>
                            </div>
                            <h3 className="font-black text-sm">{event.name}</h3>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{event.description}</p>
                            <div className="flex items-center gap-2 mt-2 text-xs">
                                <span className="bg-gray-100 px-2 py-0.5 font-bold">{event.event_type}</span>
                                <span className="text-gray-400">{event.affected_wards.length} wards affected</span>
                            </div>
                            {event.actual_damage.rainfall_mm && (
                                <div className="text-xs text-blue-600 font-bold mt-1">
                                    ☔ {String(event.actual_damage.rainfall_mm)}mm rainfall
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Validation Results */}
                <div className="col-span-8 space-y-4">
                    {loading ? (
                        <div className="bg-white border-2 border-black p-12 text-center">
                            <div className="animate-spin w-8 h-8 border-4 border-black border-t-transparent rounded-full mx-auto mb-3" />
                            <p className="font-bold">Running validation against historical data...</p>
                            <p className="text-sm text-gray-500">Fetching archived weather from Open-Meteo → running risk model</p>
                        </div>
                    ) : validation ? (
                        <>
                            {/* Accuracy Metrics */}
                            <div className="grid grid-cols-4 gap-3">
                                <div className="bg-white border-2 border-black p-3 text-center">
                                    <div className="text-xs font-bold uppercase text-gray-500">Accuracy</div>
                                    <div className="text-3xl font-black" style={{ color: Number(validation.validation.accuracy) > 70 ? '#22c55e' : '#ef4444' }}>
                                        {String(validation.validation.accuracy)}%
                                    </div>
                                </div>
                                <div className="bg-white border-2 border-blue-500 p-3 text-center">
                                    <div className="text-xs font-bold uppercase text-blue-500">Precision</div>
                                    <div className="text-3xl font-black text-blue-600">{String(validation.validation.precision)}%</div>
                                </div>
                                <div className="bg-white border-2 border-purple-500 p-3 text-center">
                                    <div className="text-xs font-bold uppercase text-purple-500">Recall</div>
                                    <div className="text-3xl font-black text-purple-600">{String(validation.validation.recall)}%</div>
                                </div>
                                <div className="bg-white border-2 border-green-500 p-3 text-center">
                                    <div className="text-xs font-bold uppercase text-green-500">Lead Time</div>
                                    <div className="text-3xl font-black text-green-600">{String(validation.validation.lead_time_hours)}h</div>
                                </div>
                            </div>

                            {/* Would Have Predicted */}
                            <div className={`border-2 p-4 flex items-center gap-3 ${validation.validation.would_have_predicted
                                ? 'bg-green-50 border-green-500'
                                : 'bg-red-50 border-red-500'
                                }`}>
                                {validation.validation.would_have_predicted
                                    ? <CheckCircle className="w-6 h-6 text-green-600" />
                                    : <XCircle className="w-6 h-6 text-red-600" />
                                }
                                <div>
                                    <div className="font-black text-sm">
                                        {validation.validation.would_have_predicted
                                            ? `Model WOULD have predicted "${validation.event.name}"`
                                            : `Model may have missed "${validation.event.name}"`
                                        }
                                    </div>
                                    <div className="text-xs text-gray-600">
                                        Average risk for affected wards: {String(validation.validation.avg_risk_affected_wards)}% |
                                        Lead time: {String(validation.validation.lead_time_hours)} hours before event
                                    </div>
                                </div>
                            </div>

                            {/* Confusion Matrix */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-green-50 border-2 border-green-300 p-3 flex items-center gap-2">
                                    <CheckCircle className="w-5 h-5 text-green-600" />
                                    <div>
                                        <div className="text-sm font-bold">True Positives: {String(validation.validation.true_positives)}</div>
                                        <div className="text-xs text-gray-500">Correctly flagged as at-risk</div>
                                    </div>
                                </div>
                                <div className="bg-red-50 border-2 border-red-300 p-3 flex items-center gap-2">
                                    <XCircle className="w-5 h-5 text-red-600" />
                                    <div>
                                        <div className="text-sm font-bold">False Negatives: {String(validation.validation.false_negatives)}</div>
                                        <div className="text-xs text-gray-500">Missed — actually affected</div>
                                    </div>
                                </div>
                            </div>

                            {/* Ward Predictions Chart */}
                            <div className="bg-white border-2 border-black p-4" style={{ height: 300 }}>
                                <h4 className="font-black text-sm uppercase mb-2">Ward-Level Predictions vs Actual</h4>
                                <ResponsiveContainer width="100%" height="90%">
                                    <BarChart data={validation.ward_predictions}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="ward_name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10 }} />
                                        <YAxis domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
                                        <Tooltip formatter={(v: number) => [`${v}%`]} />
                                        <Bar dataKey="predicted_risk" name="Model Prediction">
                                            {validation.ward_predictions.map((wp, i) => (
                                                <Cell key={i} fill={wp.actually_affected ? '#22c55e' : getRiskColor(wp.predicted_risk)} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Ward Detail Table */}
                            <div className="bg-white border-2 border-black overflow-hidden">
                                <div className="p-3 bg-black text-white font-black text-sm uppercase">
                                    Ward-by-Ward Analysis
                                </div>
                                <div className="overflow-auto" style={{ maxHeight: 300 }}>
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-100 sticky top-0">
                                            <tr>
                                                <th className="text-left p-2 font-bold">Ward</th>
                                                <th className="text-center p-2 font-bold">Predicted</th>
                                                <th className="text-center p-2 font-bold">Actually Hit</th>
                                                <th className="text-center p-2 font-bold">Result</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {validation.ward_predictions.map(wp => (
                                                <tr key={wp.ward_id} className="border-t border-gray-100">
                                                    <td className="p-2 font-bold">{wp.ward_name}</td>
                                                    <td className="p-2 text-center">
                                                        <span className="font-bold" style={{ color: getRiskColor(wp.predicted_risk) }}>
                                                            {wp.predicted_risk}%
                                                        </span>
                                                    </td>
                                                    <td className="p-2 text-center">
                                                        {wp.actually_affected ? 'Yes' : '—'}
                                                    </td>
                                                    <td className={`p-2 text-center font-bold ${getClassColor(wp.classification)}`}>
                                                        {wp.classification.replace('_', ' ')}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="bg-white border-2 border-black p-12 text-center text-gray-500">
                            <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p className="font-bold">Select a historical event to validate</p>
                            <p className="text-sm">The model will be tested against real weather data from that event</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
