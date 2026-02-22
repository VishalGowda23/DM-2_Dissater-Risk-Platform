import { useEffect, useState } from 'react';
import { AlertTriangle, Droplets, Thermometer, Users, MapPin, TrendingUp, Activity } from 'lucide-react';
import { useLang, hazardKey, wardName } from '@/lib/i18n';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { API_BASE_URL, type RiskData, type Ward, type RiskSummary as RiskSummaryType, getRiskColor } from '../lib/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface RiskSummaryProps {
  riskData: RiskData[];
  wards: Ward[];
}

export default function RiskSummary({ riskData, wards }: RiskSummaryProps) {
  const { t, lang } = useLang();
  const [summary, setSummary] = useState<RiskSummaryType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/risk/summary`);
      const data = await res.json();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const riskDistribution = [
    { name: t('low030'), count: riskData.filter(r => r.top_risk_score <= 30).length, color: '#22c55e' },
    { name: t('moderate3160'), count: riskData.filter(r => r.top_risk_score > 30 && r.top_risk_score <= 60).length, color: '#eab308' },
    { name: t('high6180'), count: riskData.filter(r => r.top_risk_score > 60 && r.top_risk_score <= 80).length, color: '#f97316' },
    { name: t('critical81100'), count: riskData.filter(r => r.top_risk_score > 80).length, color: '#ef4444' },
  ];

  const topRiskWards = [...riskData]
    .sort((a, b) => b.top_risk_score - a.top_risk_score)
    .slice(0, 10);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'critical':
        return <Badge className="bg-red-600 text-white rounded-none">{t('statusCritical')}</Badge>;
      case 'high':
        return <Badge className="bg-orange-500 text-white rounded-none">{t('statusHigh')}</Badge>;
      default:
        return <Badge className="bg-green-500 text-white rounded-none">{t('statusNormal')}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-white border-2 border-black p-3 sm:p-4 gap-2 sm:gap-0">
        <div>
          <h2 className="text-2xl font-black uppercase">{t('cityRiskSummary')}</h2>
          <p className="text-gray-500">{t('puneMunicipal')}</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500 mb-1">{t('overallStatus')}</div>
          {getStatusBadge(summary?.overall_status || 'normal')}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <Card className="border-2 border-black rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-gray-500">{t('totalWards')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <MapPin className="w-8 h-8 text-gray-400" />
              <span className="text-3xl font-black">{summary?.total_wards || wards.length}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-black rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-gray-500">{t('totalPopulation')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8 text-gray-400" />
              <span className="text-3xl font-black">
                {((summary?.total_population || wards.reduce((acc, w) => acc + (w.population || 0), 0)) / 1000000).toFixed(2)}M
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-black rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-gray-500">{t('criticalWards')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <span className="text-3xl font-black text-red-600">
                {summary?.critical_wards?.count || riskData.filter(r => r.top_risk_score > 80).length}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-black rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-gray-500">{t('highRiskWardsLabel')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-orange-500" />
              <span className="text-3xl font-black text-orange-600">
                {summary?.high_risk_wards?.count || riskData.filter(r => r.top_risk_score > 60 && r.top_risk_score <= 80).length}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* Risk Distribution Chart */}
        <Card className="border-2 border-black rounded-none">
          <CardHeader>
            <CardTitle className="font-black uppercase">{t('riskDistribution')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count">
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Average Risks */}
        <Card className="border-2 border-black rounded-none">
          <CardHeader>
            <CardTitle className="font-black uppercase">{t('avgRiskByHazard')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Droplets className="w-5 h-5 text-blue-500" />
                    <span className="font-bold">{t('floodRisk')}</span>
                  </div>
                  <span className="text-2xl font-black">
                    {summary?.average_risks?.flood?.toFixed(1) || 
                     (riskData.reduce((acc, r) => acc + (r.flood?.event || 0), 0) / riskData.length).toFixed(1)}%
                  </span>
                </div>
                <div className="h-4 bg-gray-200 overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${summary?.average_risks?.flood || 50}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Thermometer className="w-5 h-5 text-orange-500" />
                    <span className="font-bold">{t('heatRisk')}</span>
                  </div>
                  <span className="text-2xl font-black">
                    {summary?.average_risks?.heat?.toFixed(1) || 
                     (riskData.reduce((acc, r) => acc + (r.heat?.event || 0), 0) / riskData.length).toFixed(1)}%
                  </span>
                </div>
                <div className="h-4 bg-gray-200 overflow-hidden">
                  <div 
                    className="h-full bg-orange-500 transition-all"
                    style={{ width: `${summary?.average_risks?.heat || 50}%` }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Risk Wards */}
      <Card className="border-2 border-black rounded-none">
        <CardHeader>
          <CardTitle className="font-black uppercase">{t('top10Wards')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-black">
                  <th className="text-left py-2 px-4 font-bold">{t('rank')}</th>
                  <th className="text-left py-2 px-4 font-bold">{t('ward')}</th>
                  <th className="text-left py-2 px-4 font-bold">{t('topHazard')}</th>
                  <th className="text-right py-2 px-4 font-bold">{t('riskScore')}</th>
                  <th className="text-right py-2 px-4 font-bold">{t('population')}</th>
                </tr>
              </thead>
              <tbody>
                {topRiskWards.map((ward, idx) => (
                  <tr key={ward.ward_id} className="border-b border-gray-200">
                    <td className="py-3 px-4">
                      <span className="w-6 h-6 bg-black text-white inline-flex items-center justify-center font-bold text-sm">
                        {idx + 1}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium">{wardName(ward, lang)}</td>
                    <td className="py-3 px-4">
                      <Badge 
                        variant="outline" 
                        className={`rounded-none uppercase font-bold ${
                          ward.top_hazard === 'flood' 
                            ? 'border-blue-500 text-blue-600' 
                            : ward.top_hazard === 'heat'
                            ? 'border-orange-500 text-orange-600'
                            : 'border-gray-500 text-gray-600'
                        }`}
                      >
                        {t(hazardKey(ward.top_hazard))}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span 
                        className="font-black px-2 py-1"
                        style={{ 
                          backgroundColor: getRiskColor(ward.top_risk_score),
                          color: ward.top_risk_score > 60 ? 'white' : 'black'
                        }}
                      >
                        {ward.top_risk_score?.toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {ward.population?.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
