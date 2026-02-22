import { useState } from 'react';
import { Settings, Truck, Home, Thermometer, Droplets, Activity, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react';
import { useLang, wardName, resourceKey } from '@/lib/i18n';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { API_BASE_URL, type RiskData, type Ward, type OptimizationResult } from '../lib/types';
import { toast } from 'sonner';

interface ResourceOptimizerProps {
  riskData: RiskData[];
  wards: Ward[];
}

export default function ResourceOptimizer({ riskData: _riskData }: ResourceOptimizerProps) {
  const { t, lang } = useLang();
  const [resources, setResources] = useState({
    pumps: 25,
    buses: 15,
    relief_camps: 12,
    cooling_centers: 20,
    medical_units: 8,
  });

  const [useDelta, setUseDelta] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resources,
          scenario: { use_delta: useDelta }
        })
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
        toast.success(t('optimizeSuccess'));
      } else {
        toast.error(t('optimizeFailed'));
      }
    } catch (error) {
      toast.error(t('optimizeError'));
    } finally {
      setLoading(false);
    }
  };

  const handleResourceChange = (key: string, value: string) => {
    const num = parseInt(value) || 0;
    setResources(prev => ({ ...prev, [key]: num }));
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'pumps':
        return <Droplets className="w-5 h-5 text-blue-500" />;
      case 'buses':
        return <Truck className="w-5 h-5 text-green-500" />;
      case 'relief_camps':
        return <Home className="w-5 h-5 text-purple-500" />;
      case 'cooling_centers':
        return <Thermometer className="w-5 h-5 text-orange-500" />;
      case 'medical_units':
        return <Activity className="w-5 h-5 text-red-500" />;
      default:
        return <Settings className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration Panel */}
      <Card className="border-2 border-black rounded-none">
        <CardHeader>
          <CardTitle className="font-black uppercase flex items-center gap-2">
            <Settings className="w-5 h-5" />
            {t('resourceConfig')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
            {Object.entries(resources).map(([key, value]) => (
              <div key={key} className="space-y-2">
                <Label className="font-bold uppercase text-xs flex items-center gap-1">
                  {getResourceIcon(key)}
                  {t(resourceKey(key))}
                </Label>
                <Input
                  type="number"
                  value={value}
                  onChange={(e) => handleResourceChange(key, e.target.value)}
                  className="border-2 border-black rounded-none font-mono"
                  min={0}
                />
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Switch
                checked={useDelta}
                onCheckedChange={setUseDelta}
              />
              <div>
                <Label className="font-medium block">
                  {t('prioritizeSurging')}
                </Label>
                <p className="text-xs text-gray-500 mt-0.5">
                  {useDelta ? t('prioritizeSurgingOn') : t('prioritizeSurgingOff')}
                </p>
              </div>
            </div>

            <Button
              onClick={handleOptimize}
              disabled={loading}
              className="bg-black text-white rounded-none font-bold hover:bg-gray-800"
            >
              {loading ? (
                <Activity className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              {t('runOptimization')}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Allocation skipped — all wards low risk */}
          {result.summary.allocation_skipped ? (
            <Card className="border-2 border-green-600 rounded-none">
              <CardContent className="pt-6 pb-6">
                <div className="flex items-center gap-3 mb-2">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                  <div className="text-lg font-black uppercase text-green-700">{t('noDeployRequired')}</div>
                </div>
                <p className="text-sm text-gray-700">
                  {t('noDeployDesc')} ({result.summary.activation_threshold}).
                  {t('highestRecordedRisk')} <span className="font-bold">{result.summary.max_risk}</span>.
                  {t('noDeployUntilDeter')}
                </p>
              </CardContent>
            </Card>
          ) : (
          <>
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('totalWards')}</div>
                <div className="text-3xl font-black">{result.summary.total_wards}</div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('criticalWards')}</div>
                <div className="text-3xl font-black text-red-600">{result.summary.critical_wards}</div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('highestNeed')}</div>
                <div className="text-lg font-black truncate">
                  {(() => { const w = result.ward_allocations.find(w => w.ward_id === result.summary.highest_need_ward); return w ? wardName(w, lang) : ''; })()}
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">{t('deployed')}</div>
                <div className="text-3xl font-black">
                  {Object.values(result.total_allocated).reduce((a, b) => a + b, 0)}
                </div>
                <div className="text-xs text-gray-400 mt-1">{t('unitsAllocated')}</div>
              </CardContent>
            </Card>
          </div>

          {/* Resource Allocation Summary */}
          <Card className="border-2 border-black rounded-none">
            <CardHeader>
              <CardTitle className="font-black uppercase">{t('allocationSummary')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                {Object.entries(result.total_resources).map(([type, total]) => (
                  <div key={type} className="border-2 border-gray-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      {getResourceIcon(type)}
                      <span className="font-bold uppercase text-sm">{t(resourceKey(type))}</span>
                    </div>
                    <div className="text-2xl font-black">
                      {result.total_allocated[type] || 0} / {total}
                    </div>
                    <div className="text-xs text-gray-500">
                      {((result.total_allocated[type] || 0) / total * 100).toFixed(0)}% {t('allocated')}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Resource Gap / Deficit Analysis */}
          {result.resource_gap && result.resource_gap_summary && (
            <Card className="border-2 border-black rounded-none">
              <CardHeader>
                <CardTitle className="font-black uppercase flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  {t('resourceGapAnalysis')}
                </CardTitle>
                <div className="flex items-center gap-2 sm:gap-4 mt-2 flex-wrap">
                  <div className="text-sm text-gray-600">
                    {t('overallCoverage')}:{' '}
                    <span className={`font-black ${
                      result.resource_gap_summary.overall_coverage_pct >= 80 ? 'text-green-600' :
                      result.resource_gap_summary.overall_coverage_pct >= 50 ? 'text-amber-600' :
                      'text-red-600'
                    }`}>
                      {result.resource_gap_summary.overall_coverage_pct}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {t('totalNeeded')}: <span className="font-black">{result.resource_gap_summary.total_required}</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {t('totalAvailable')}: <span className="font-black">{result.resource_gap_summary.total_available}</span>
                  </div>
                  {result.resource_gap_summary.total_gap > 0 && (
                    <Badge variant="outline" className="border-red-600 text-red-600 rounded-none font-bold">
                      {t('deficit')}: {result.resource_gap_summary.total_gap} units
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-4">
                  {Object.entries(result.resource_gap).map(([type, gapData]) => {
                    const hasGap = gapData.total_gap > 0;
                    const topDeficitWards = gapData.ward_requirements
                      .filter(w => w.gap > 0)
                      .slice(0, 5);

                    return (
                      <div key={type} className={`border-2 p-4 ${hasGap ? 'border-red-300 bg-red-50' : 'border-green-300 bg-green-50'}`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            {getResourceIcon(type)}
                            <span className="font-bold uppercase text-sm">{t(resourceKey(type))}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-sm">
                              <span className="text-gray-500">{t('available')}:</span>{' '}
                              <span className="font-black">{gapData.total_available}</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-gray-500">{t('required')}:</span>{' '}
                              <span className="font-black">{gapData.total_required}</span>
                            </div>
                            {hasGap ? (
                              <Badge variant="outline" className="border-red-600 text-red-600 rounded-none font-bold text-xs">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                +{gapData.total_gap} {gapData.unit} {t('unitsNeeded')}
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="border-green-600 text-green-600 rounded-none font-bold text-xs">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                {t('sufficient')}
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Coverage bar */}
                        <div className="w-full bg-gray-200 h-3 mb-3">
                          <div
                            className={`h-3 ${
                              gapData.coverage_pct >= 80 ? 'bg-green-500' :
                              gapData.coverage_pct >= 50 ? 'bg-amber-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(100, gapData.coverage_pct)}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-500 mb-2">
                          {gapData.coverage_pct}% {t('coverageLabel')}
                        </div>

                        {/* Top deficit wards */}
                        {topDeficitWards.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs font-bold uppercase text-gray-500 mb-1">
                              {t('topWardsNeeding')} {t(resourceKey(type))}:
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {topDeficitWards.map(w => (
                                <span key={w.ward_id} className="inline-flex items-center gap-1 text-xs bg-white border border-gray-300 px-2 py-1 font-mono">
                                  <span className="font-bold">{wardName(w as unknown as { ward_name: string; ward_name_marathi?: string }, lang) || w.ward_id}</span>
                                  <span className="text-red-600 font-bold">+{w.gap}</span>
                                  <span className="text-gray-400">({w.allocated}/{w.required})</span>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Ward Allocations Table */}
          <Card className="border-2 border-black rounded-none">
            <CardHeader>
              <CardTitle className="font-black uppercase">{t('wardwiseAllocations')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-black bg-gray-100">
                      <th className="text-left py-3 px-4 font-bold">{t('rank')}</th>
                      <th className="text-left py-3 px-4 font-bold">{t('ward')}</th>
                      <th className="text-left py-3 px-4 font-bold">{t('needScore')}</th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Droplets className="w-4 h-4 inline text-blue-500" /> {t('resPumps')}
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Truck className="w-4 h-4 inline text-green-500" /> {t('resBuses')}
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Home className="w-4 h-4 inline text-purple-500" /> {t('resCamps')}
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Thermometer className="w-4 h-4 inline text-orange-500" /> {t('resCooling')}
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Activity className="w-4 h-4 inline text-red-500" /> {t('resMedical')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.ward_allocations.map((ward, idx) => (
                      <tr key={ward.ward_id} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <span className="w-6 h-6 bg-black text-white inline-flex items-center justify-center font-bold text-sm">
                            {idx + 1}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium">{wardName(ward, lang)}</div>
                          <div className="text-xs text-gray-500">{t('popLabel')} {ward.population?.toLocaleString()}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-mono font-bold">{ward.need_score?.toFixed(1)}</div>
                          {ward.risk?.delta > 10 && (
                            <Badge variant="outline" className="text-xs text-red-600 border-red-600 rounded-none">
                              +{ward.risk.delta?.toFixed(0)}%
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {ward.resources.pumps?.allocated > 0 ? (
                            <span className="font-bold text-blue-600">{ward.resources.pumps.allocated}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {ward.resources.buses?.allocated > 0 ? (
                            <span className="font-bold text-green-600">{ward.resources.buses.allocated}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {ward.resources.relief_camps?.allocated > 0 ? (
                            <span className="font-bold text-purple-600">{ward.resources.relief_camps.allocated}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {ward.resources.cooling_centers?.allocated > 0 ? (
                            <span className="font-bold text-orange-600">{ward.resources.cooling_centers.allocated}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {ward.resources.medical_units?.allocated > 0 ? (
                            <span className="font-bold text-red-600">{ward.resources.medical_units.allocated}</span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Explanations */}
          {Object.keys(result.explanations).length > 0 && (
            <Card className="border-2 border-black rounded-none bg-yellow-50">
              <CardHeader>
                <CardTitle className="font-black uppercase">{t('allocationRationale')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(result.explanations).map(([key, text]) => (
                    <div key={key} className="flex items-start gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm">{text}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          </>
          )}
        </div>
      )}
    </div>
  );
}
