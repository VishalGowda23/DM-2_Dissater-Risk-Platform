import { useState } from 'react';
import { Activity, Play, RotateCcw, Droplets, Thermometer, TrendingUp, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { API_BASE_URL, type RiskData, type Ward, type ScenarioResult, getRiskColor } from '../lib/types';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ScenarioSimulatorProps {
  riskData: RiskData[];
  wards: Ward[];
}

export default function ScenarioSimulator({ riskData: _riskData }: ScenarioSimulatorProps) {
  const [rainfallMultiplier, setRainfallMultiplier] = useState(1.0);
  const [tempAnomaly, setTempAnomaly] = useState(0);
  const [drainageEfficiency, setDrainageEfficiency] = useState(1.0);
  const [populationGrowth, setPopulationGrowth] = useState(0);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);

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
        toast.success('Scenario simulation complete!');
      } else {
        toast.error('Scenario simulation failed');
      }
    } catch (error) {
      toast.error('Error running scenario');
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
  };

  const getScenarioChartData = () => {
    if (!result?.results) return [];

    return result.results.slice(0, 10).map(item => ({
      name: item.baseline.ward_name,
      baseline: item.baseline.top_risk_score,
      scenario: item.scenario.top_risk_score,
      delta: item.scenario.top_risk_score - item.baseline.top_risk_score
    }));
  };

  return (
    <div className="space-y-6">
      {/* Scenario Controls */}
      <Card className="border-2 border-black rounded-none">
        <CardHeader>
          <CardTitle className="font-black uppercase flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Scenario Parameters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-8">
            {/* Rainfall Multiplier */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<Droplets className="w-4 h-4 text-blue-500" />}>
                  Rainfall Multiplier
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
                <span>0.5x (Drought)</span>
                <span>1.0x (Normal)</span>
                <span>3.0x (Extreme)</span>
              </div>
            </div>

            {/* Temperature Anomaly */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<Thermometer className="w-4 h-4 text-orange-500" />}>
                  Temperature Anomaly
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
                <span>0°C (Normal)</span>
                <span>+5°C (Heatwave)</span>
                <span>+10°C (Extreme)</span>
              </div>
            </div>

            {/* Drainage Efficiency */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<TrendingUp className="w-4 h-4 text-green-500" />}>
                  Drainage Efficiency
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
                <span>0.5x (Blocked)</span>
                <span>1.0x (Normal)</span>
                <span>1.5x (Improved)</span>
              </div>
            </div>

            {/* Population Growth */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label icon={<Activity className="w-4 h-4 text-purple-500" />}>
                  Population Growth
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
                <span>0% (Current)</span>
                <span>25% (Growth)</span>
                <span>50% (Rapid)</span>
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
              Run Scenario Simulation
            </Button>
            <Button
              onClick={resetScenario}
              variant="outline"
              className="border-2 border-black rounded-none font-bold"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Scenario Results */}
      {result && result.aggregate_impact && (
        <div className="space-y-6">
          {/* Impact Summary */}
          <div className="grid grid-cols-4 gap-4">
            <Card className={`border-2 rounded-none ${result.aggregate_impact.avg_flood_risk_change > 10
                ? 'border-red-500 bg-red-50'
                : 'border-black'
              }`}>
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">Flood Risk Change</div>
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
                <div className="text-sm text-gray-500 uppercase font-bold">Heat Risk Change</div>
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
                <div className="text-sm text-gray-500 uppercase font-bold">Newly Critical Wards</div>
                <div className={`text-3xl font-black ${result.aggregate_impact.wards_newly_critical > 0 ? 'text-red-600' : ''
                  }`}>
                  {result.aggregate_impact.wards_newly_critical}
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">Total Wards</div>
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
                    <h3 className="font-bold text-red-600 uppercase">High Impact Scenario</h3>
                    <p className="text-sm text-red-700">
                      This scenario shows significant risk increases. Consider pre-positioning resources
                      and activating emergency protocols.
                    </p>
                  </div>
                </div>
              </div>
            )}

          {/* Comparison Chart */}
          <Card className="border-2 border-black rounded-none">
            <CardHeader>
              <CardTitle className="font-black uppercase">Top 10 Wards: Baseline vs Scenario</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={getScenarioChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-45} textAnchor="end" height={80} />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="baseline" name="Baseline" fill="#6b7280" />
                    <Bar dataKey="scenario" name="Scenario" fill="#ef4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Results Table */}
          {result.results && (
            <Card className="border-2 border-black rounded-none">
              <CardHeader>
                <CardTitle className="font-black uppercase">Detailed Ward Impact</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b-2 border-black bg-gray-100">
                        <th className="text-left py-3 px-4 font-bold">Ward</th>
                        <th className="text-right py-3 px-4 font-bold">Baseline Risk</th>
                        <th className="text-right py-3 px-4 font-bold">Scenario Risk</th>
                        <th className="text-right py-3 px-4 font-bold">Change</th>
                        <th className="text-center py-3 px-4 font-bold">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map(({ baseline, scenario }) => {
                        const change = scenario.top_risk_score - baseline.top_risk_score;
                        const isCritical = scenario.top_risk_score > 80 && baseline.top_risk_score <= 80;

                        return (
                          <tr key={baseline.ward_id} className="border-b border-gray-200">
                            <td className="py-3 px-4 font-medium">{baseline.ward_name}</td>
                            <td className="py-3 px-4 text-right">
                              <span
                                className="px-2 py-1 font-bold"
                                style={{
                                  backgroundColor: getRiskColor(baseline.top_risk_score),
                                  color: baseline.top_risk_score > 60 ? 'white' : 'black'
                                }}
                              >
                                {baseline.top_risk_score?.toFixed(0)}%
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span
                                className="px-2 py-1 font-bold"
                                style={{
                                  backgroundColor: getRiskColor(scenario.top_risk_score),
                                  color: scenario.top_risk_score > 60 ? 'white' : 'black'
                                }}
                              >
                                {scenario.top_risk_score?.toFixed(0)}%
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className={`font-mono font-bold ${change > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                {change > 0 ? '+' : ''}{change.toFixed(1)}%
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              {isCritical && (
                                <Badge className="bg-red-600 text-white rounded-none">
                                  NEW CRITICAL
                                </Badge>
                              )}
                              {scenario.top_risk_score > 80 && baseline.top_risk_score > 80 && (
                                <Badge variant="outline" className="border-red-600 text-red-600 rounded-none">
                                  STAYS CRITICAL
                                </Badge>
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
