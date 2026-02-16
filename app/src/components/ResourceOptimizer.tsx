import { useState } from 'react';
import { Settings, Truck, Home, Thermometer, Droplets, Activity, CheckCircle } from 'lucide-react';
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
        toast.success('Optimization complete!');
      } else {
        toast.error('Optimization failed');
      }
    } catch (error) {
      toast.error('Error running optimization');
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
            Resource Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4 mb-6">
            {Object.entries(resources).map(([key, value]) => (
              <div key={key} className="space-y-2">
                <Label className="font-bold uppercase text-xs flex items-center gap-1">
                  {getResourceIcon(key)}
                  {key.replace('_', ' ')}
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
              <Label className="font-medium">
                Use Risk Delta for allocation (prioritize surging wards)
              </Label>
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
              Run Optimization
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-4 gap-4">
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">Total Wards</div>
                <div className="text-3xl font-black">{result.summary.total_wards}</div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">Critical Wards</div>
                <div className="text-3xl font-black text-red-600">{result.summary.critical_wards}</div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">Highest Need</div>
                <div className="text-lg font-black truncate">
                  {result.ward_allocations.find(w => w.ward_id === result.summary.highest_need_ward)?.ward_name}
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black rounded-none">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-500 uppercase font-bold">Resources Allocated</div>
                <div className="text-3xl font-black">
                  {Object.values(result.total_allocated).reduce((a, b) => a + b, 0)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Resource Allocation Summary */}
          <Card className="border-2 border-black rounded-none">
            <CardHeader>
              <CardTitle className="font-black uppercase">Allocation Summary by Resource Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4">
                {Object.entries(result.total_resources).map(([type, total]) => (
                  <div key={type} className="border-2 border-gray-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      {getResourceIcon(type)}
                      <span className="font-bold uppercase text-sm">{type.replace('_', ' ')}</span>
                    </div>
                    <div className="text-2xl font-black">
                      {result.total_allocated[type] || 0} / {total}
                    </div>
                    <div className="text-xs text-gray-500">
                      {((result.total_allocated[type] || 0) / total * 100).toFixed(0)}% allocated
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Ward Allocations Table */}
          <Card className="border-2 border-black rounded-none">
            <CardHeader>
              <CardTitle className="font-black uppercase">Ward-wise Allocations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-black bg-gray-100">
                      <th className="text-left py-3 px-4 font-bold">Rank</th>
                      <th className="text-left py-3 px-4 font-bold">Ward</th>
                      <th className="text-left py-3 px-4 font-bold">Need Score</th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Droplets className="w-4 h-4 inline text-blue-500" /> Pumps
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Truck className="w-4 h-4 inline text-green-500" /> Buses
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Home className="w-4 h-4 inline text-purple-500" /> Camps
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Thermometer className="w-4 h-4 inline text-orange-500" /> Cooling
                      </th>
                      <th className="text-center py-3 px-4 font-bold">
                        <Activity className="w-4 h-4 inline text-red-500" /> Medical
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
                          <div className="font-medium">{ward.ward_name}</div>
                          <div className="text-xs text-gray-500">Pop: {ward.population?.toLocaleString()}</div>
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
                <CardTitle className="font-black uppercase">Allocation Rationale</CardTitle>
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
        </div>
      )}
    </div>
  );
}
