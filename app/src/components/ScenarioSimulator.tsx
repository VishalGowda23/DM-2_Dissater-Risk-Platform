import { useState } from 'react';
import { Activity, Play, RotateCcw, Droplets, Thermometer, TrendingUp, AlertTriangle, Zap } from 'lucide-react';
import { useLang, wardName, type TranslationKey } from '@/lib/i18n';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { API_BASE_URL, type RiskData, type Ward, type ScenarioResult, getRiskColor } from '../lib/types';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';

interface ScenarioSimulatorProps {
  riskData: RiskData[];
  wards: Ward[];
}

const PRESETS = [
  { labelKey: 'presetHeavyMonsoon' as TranslationKey, icon: '🌧️', rain: 2.5, temp: 0, drain: 1.0, pop: 0, descKey: 'presetHeavyMonsoonDesc' as TranslationKey },
  { labelKey: 'presetCloudburst' as TranslationKey, icon: '⛈️', rain: 3.0, temp: 0, drain: 0.7, pop: 0, descKey: 'presetCloudburstDesc' as TranslationKey },
  { labelKey: 'presetHeatwave' as TranslationKey, icon: '🔥', rain: 1.0, temp: 6, drain: 1.0, pop: 0, descKey: 'presetHeatwaveDesc' as TranslationKey },
  { labelKey: 'presetCompound' as TranslationKey, icon: '⚠️', rain: 2.0, temp: 3, drain: 0.8, pop: 10, descKey: 'presetCompoundDesc' as TranslationKey },
  { labelKey: 'presetDrainage' as TranslationKey, icon: '🔧', rain: 1.0, temp: 0, drain: 1.4, pop: 0, descKey: 'presetDrainageDesc' as TranslationKey },
];

export default function ScenarioSimulator({ riskData: _riskData }: ScenarioSimulatorProps) {
  const { t, lang } = useLang();
  const [rainfallMultiplier, setRainfallMultiplier] = useState(1.0);
  const [tempAnomaly, setTempAnomaly] = useState(0);
  const [drainageEfficiency, setDrainageEfficiency] = useState(1.0);
  const [populationGrowth, setPopulationGrowth] = useState(0);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setRainfallMultiplier(preset.rain);
    setTempAnomaly(preset.temp);
    setDrainageEfficiency(preset.drain);
    setPopulationGrowth(preset.pop);
    setActivePreset(t(preset.labelKey));
    setResult(null);
  };

  const runScenario = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_key: 'custom',
          custom_params: {
            rainfall_multiplier: rainfallMultiplier,
            temp_anomaly_addition: tempAnomaly,
            drainage_efficiency_multiplier: drainageEfficiency,
            population_growth_pct: populationGrowth
          }
        })
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
        toast.success(t('scenarioSuccess'));
      } else {
        toast.error(t('scenarioFailed'));
      }
    } catch (error) {
      toast.error(t('scenarioError'));
    } finally {
      setLoading(false);
    }
  };

  const resetScenario = () => {
    setRainfallMultiplier(1.0);
    setTempAnomaly(0);
    setDrainageEfficiency(1.0);
    setPopulationGrowth(0);
    setResult(null);
    setActivePreset(null);
  };

  const isNeutral = rainfallMultiplier === 1.0 && tempAnomaly === 0 && drainageEfficiency === 1.0 && populationGrowth === 0;

  const getScenarioChartData = () => {
    if (!result?.results) return [];

    // Show top 10 wards sorted by absolute combined delta (most impacted first)
    return result.results.slice(0, 10).map(item => {
      const floodDelta = (item.scenario.flood?.delta ?? 0);
      const heatDelta = (item.scenario.heat?.delta ?? 0);
      const wn = wardName(item.baseline, lang);
      return {
        name: wn.length > 12
          ? wn.slice(0, 11) + '…'
          : wn,
        fullName: wn,
        [t('floodDeltaHeader')]: Number(floodDelta.toFixed(1)),
        [t('heatDeltaHeader')]: Number(heatDelta.toFixed(1)),
        baselineRisk: item.baseline.top_risk_score,
        scenarioRisk: item.scenario.top_risk_score,
      };
    });
  };

  const getScenarioDescription = (): string => {
    if (isNeutral) return t('scenarioDescNeutral');
    const parts: string[] = [];
    if (rainfallMultiplier > 1) parts.push(`${rainfallMultiplier.toFixed(1)}× ${t('scenarioDescRainfall')}`);
    if (rainfallMultiplier < 1) parts.push(`${t('scenarioDescReducedRain')} (${rainfallMultiplier.toFixed(1)}×)`);
    if (tempAnomaly > 0) parts.push(`+${tempAnomaly}°C ${t('scenarioDescTempRise')}`);
    if (drainageEfficiency < 1) parts.push(`${t('scenarioDescDegradedDrain')} (${((1 - drainageEfficiency) * 100).toFixed(0)}%)`);
    if (drainageEfficiency > 1) parts.push(`${t('scenarioDescImprovedDrain')} (+${((drainageEfficiency - 1) * 100).toFixed(0)}%)`);
    if (populationGrowth > 0) parts.push(`${populationGrowth}% ${t('scenarioDescPopGrowth')}`);
    return `${t('scenarioDescSimulating')} ${parts.join(' + ')}`;
  };

  return (
    <div className="space-y-6">
      {/* Scenario Controls */}
      <Card className="border-2 border-black rounded-none">
        <CardHeader>
          <CardTitle className="font-black uppercase flex items-center gap-2">
            <Activity className="w-5 h-5" />
            {t('scenarioParams')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Quick Presets */}
          <div className="mb-6">
            <div className="text-xs font-bold uppercase text-gray-500 mb-2">{t('quickPresets')}</div>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map(p => (
                <button
                  key={p.labelKey}
                  onClick={() => applyPreset(p)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold border-2 transition-colors ${
                    activePreset === t(p.labelKey)
                      ? 'border-black bg-black text-white'
                      : 'border-gray-300 bg-white hover:border-black'
                  }`}
                  title={t(p.descKey)}
                >
                  <span>{p.icon}</span> {t(p.labelKey)}
                </button>
              ))}
            </div>
          </div>

          {/* Scenario description */}
          <div className="mb-6 px-3 py-2 bg-gray-50 border border-gray-200 text-sm text-gray-700">
            <Zap className="w-3.5 h-3.5 inline mr-1 -mt-0.5 text-gray-500" />
            {getScenarioDescription()}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            {/* Rainfall Multiplier */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<Droplets className="w-4 h-4 text-blue-500" />}>
                  {t('rainfallMultiplier')}
                </Label>
                <Badge variant="outline" className="rounded-none font-mono">
                  {rainfallMultiplier.toFixed(1)}x
                </Badge>
              </div>
              <Slider
                value={[rainfallMultiplier]}
                onValueChange={([v]) => setRainfallMultiplier(v)}
                min={0.5}
                max={3.0}
                step={0.1}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0.5x ({t('sliderDrought')})</span>
                <span>1.0x ({t('sliderNormal')})</span>
                <span>3.0x ({t('sliderExtreme')})</span>
              </div>
            </div>

            {/* Temperature Anomaly */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<Thermometer className="w-4 h-4 text-orange-500" />}>
                  {t('tempAnomaly')}
                </Label>
                <Badge variant="outline" className="rounded-none font-mono">
                  +{tempAnomaly.toFixed(1)}°C
                </Badge>
              </div>
              <Slider
                value={[tempAnomaly]}
                onValueChange={([v]) => setTempAnomaly(v)}
                min={0}
                max={10}
                step={0.5}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0°C ({t('sliderNormal')})</span>
                <span>+5°C ({t('sliderHeatwave')})</span>
                <span>+10°C ({t('sliderExtreme')})</span>
              </div>
            </div>

            {/* Drainage Efficiency */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<TrendingUp className="w-4 h-4 text-green-500" />}>
                  {t('drainageEfficiency')}
                </Label>
                <Badge variant="outline" className="rounded-none font-mono">
                  {drainageEfficiency.toFixed(1)}x
                </Badge>
              </div>
              <Slider
                value={[drainageEfficiency]}
                onValueChange={([v]) => setDrainageEfficiency(v)}
                min={0.5}
                max={1.5}
                step={0.1}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0.5x ({t('sliderBlocked')})</span>
                <span>1.0x ({t('sliderNormal')})</span>
                <span>1.5x ({t('sliderImproved')})</span>
              </div>
            </div>

            {/* Population Growth */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<Activity className="w-4 h-4 text-purple-500" />}>
                  {t('populationGrowthLabel')}
                </Label>
                <Badge variant="outline" className="rounded-none font-mono">
                  +{populationGrowth.toFixed(0)}%
                </Badge>
              </div>
              <Slider
                value={[populationGrowth]}
                onValueChange={([v]) => setPopulationGrowth(v)}
                min={0}
                max={50}
                step={5}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0% ({t('sliderCurrent')})</span>
                <span>25% ({t('sliderGrowth')})</span>
                <span>50% ({t('sliderRapid')})</span>
              </div>
            </div>
          </div>

          <div className="flex gap-4 mt-8">
            <Button
              onClick={runScenario}
              disabled={loading}
              className="flex-1 bg-black text-white rounded-none font-bold hover:bg-gray-800"
            >
              {loading ? (
                <Activity className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              {t('runScenario')}
            </Button>
            <Button
              onClick={resetScenario}
              variant="outline"
              className="border-2 border-black rounded-none font-bold"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              {t('resetLabel')}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Scenario Results */}
      {result && result.aggregate_impact && (
        <div className="space-y-6">
          {/* Impact Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className={`border-2 rounded-none ${result.aggregate_impact.avg_flood_risk_change > 10
                ? 'border-red-500 bg-red-50'
                : 'border-black'
              }`}>
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('floodRiskChange')}</div>
                <div className={`text-3xl font-black ${result.aggregate_impact.avg_flood_risk_change > 10 ? 'text-red-600' : ''
                  }`}>
                  {result.aggregate_impact.avg_flood_risk_change > 0 ? '+' : ''}
                  {result.aggregate_impact.avg_flood_risk_change.toFixed(1)}%
                </div>
              </CardContent>
            </Card>

            <Card className={`border-2 rounded-none ${result.aggregate_impact.avg_heat_risk_change > 10
                ? 'border-orange-500 bg-orange-50'
                : 'border-black'
              }`}>
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('heatRiskChange')}</div>
                <div className={`text-3xl font-black ${result.aggregate_impact.avg_heat_risk_change > 10 ? 'text-orange-600' : ''
                  }`}>
                  {result.aggregate_impact.avg_heat_risk_change > 0 ? '+' : ''}
                  {result.aggregate_impact.avg_heat_risk_change.toFixed(1)}%
                </div>
              </CardContent>
            </Card>

            <Card className={`border-2 rounded-none ${result.aggregate_impact.wards_newly_critical > 0
                ? 'border-red-500 bg-red-50'
                : 'border-black'
              }`}>
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('newlyCriticalWards')}</div>
                <div className={`text-3xl font-black ${result.aggregate_impact.wards_newly_critical > 0 ? 'text-red-600' : ''
                  }`}>
                  {result.aggregate_impact.wards_newly_critical}
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('totalWards')}</div>
                <div className="text-3xl font-black">
                  {result.aggregate_impact.total_wards}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Impact Alert */}
          {(result.aggregate_impact.avg_flood_risk_change > 10 ||
            result.aggregate_impact.avg_heat_risk_change > 10) && (
              <div className="bg-red-100 border-2 border-red-500 p-4">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-8 h-8 text-red-600" />
                  <div>
                    <h3 className="font-bold text-red-600 uppercase">{t('highImpactScenario')}</h3>
                    <p className="text-sm text-red-700">
                      {t('highImpactDesc')}
                    </p>
                  </div>
                </div>
              </div>
            )}

          {/* Comparison Chart */}
          <Card className="border-2 border-black rounded-none">
            <CardHeader>
              <CardTitle className="font-black uppercase">{t('riskChangeByWard')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={getScenarioChartData()} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={['auto', 'auto']} tickFormatter={(v: number) => `${v > 0 ? '+' : ''}${v}`} />
                    <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={110} />
                    <Tooltip
                      formatter={(value: number, name: string) => [`${value > 0 ? '+' : ''}${value.toFixed(1)}`, name]}
                    />
                    <Legend />
                    <Bar dataKey={t('floodDeltaHeader')} fill="#3b82f6" radius={[0, 2, 2, 0]}>
                      {getScenarioChartData().map((entry, idx) => (
                        <Cell key={idx} fill={(entry as any)[t('floodDeltaHeader')] >= 0 ? '#3b82f6' : '#93c5fd'} />
                      ))}
                    </Bar>
                    <Bar dataKey={t('heatDeltaHeader')} fill="#f97316" radius={[0, 2, 2, 0]}>
                      {getScenarioChartData().map((entry, idx) => (
                        <Cell key={idx} fill={(entry as any)[t('heatDeltaHeader')] >= 0 ? '#f97316' : '#fdba74'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Results Table */}
          {result.results && (
            <Card className="border-2 border-black rounded-none">
              <CardHeader>
                <CardTitle className="font-black uppercase">{t('detailedWardImpact')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b-2 border-black bg-gray-100">
                        <th className="text-left py-3 px-4 font-bold">{t('ward')}</th>
                        <th className="text-right py-3 px-4 font-bold">{t('baseline')}</th>
                        <th className="text-right py-3 px-4 font-bold">{t('scenario')}</th>
                        <th className="text-right py-3 px-4 font-bold">
                          <span className="text-blue-600">{t('floodDeltaHeader')}</span>
                        </th>
                        <th className="text-right py-3 px-4 font-bold">
                          <span className="text-orange-600">{t('heatDeltaHeader')}</span>
                        </th>
                        <th className="text-center py-3 px-4 font-bold">{t('status')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map(({ baseline, scenario }) => {
                        const floodDelta = scenario.flood?.delta ?? 0;
                        const heatDelta = scenario.heat?.delta ?? 0;
                        const combinedChange = scenario.top_risk_score - baseline.top_risk_score;
                        const isCritical = scenario.top_risk_score > 80 && baseline.top_risk_score <= 80;

                        return (
                          <tr key={baseline.ward_id} className="border-b border-gray-200">
                            <td className="py-3 px-4 font-medium">{wardName(baseline, lang)}</td>
                            <td className="py-3 px-4 text-right">
                              <span
                                className="px-2 py-1 font-bold text-xs"
                                style={{
                                  backgroundColor: getRiskColor(baseline.top_risk_score),
                                  color: baseline.top_risk_score > 60 ? 'white' : 'black'
                                }}
                              >
                                {baseline.top_risk_score?.toFixed(1)}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span
                                className="px-2 py-1 font-bold text-xs"
                                style={{
                                  backgroundColor: getRiskColor(scenario.top_risk_score),
                                  color: scenario.top_risk_score > 60 ? 'white' : 'black'
                                }}
                              >
                                {scenario.top_risk_score?.toFixed(1)}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className={`font-mono font-bold text-sm ${floodDelta > 0.5 ? 'text-blue-700' : floodDelta < -0.5 ? 'text-blue-400' : 'text-gray-400'}`}>
                                {floodDelta > 0 ? '+' : ''}{floodDelta.toFixed(1)}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className={`font-mono font-bold text-sm ${heatDelta > 0.5 ? 'text-orange-700' : heatDelta < -0.5 ? 'text-orange-400' : 'text-gray-400'}`}>
                                {heatDelta > 0 ? '+' : ''}{heatDelta.toFixed(1)}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              {isCritical ? (
                                <Badge className="bg-red-600 text-white rounded-none text-[10px]">
                                  {t('statusNewCritical')}
                                </Badge>
                              ) : combinedChange > 10 ? (
                                <Badge className="bg-orange-500 text-white rounded-none text-[10px]">
                                  {t('statusHighImpact')}
                                </Badge>
                              ) : combinedChange > 0.5 ? (
                                <Badge variant="outline" className="border-orange-400 text-orange-600 rounded-none text-[10px]">
                                  {t('statusIncreased')}
                                </Badge>
                              ) : combinedChange < -0.5 ? (
                                <Badge variant="outline" className="border-green-400 text-green-600 rounded-none text-[10px]">
                                  {t('statusReduced')}
                                </Badge>
                              ) : (
                                <span className="text-[10px] text-gray-400 font-bold">{t('noChange')}</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

// Helper component for labels
function Label({ children, icon }: { children: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 font-bold uppercase text-sm">
      {icon}
      <span>{children}</span>
    </div>
  );
}
