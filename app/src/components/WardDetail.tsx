import { useState, useEffect } from 'react';
import { AlertTriangle, Droplets, Thermometer, TrendingUp, Users, MapPin, Activity, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_BASE_URL, type RiskData, type Ward, type RiskExplanation, getRiskColor, getRiskCategory } from '../lib/types';

interface WardDetailProps {
  ward: Ward | null;
  riskData: RiskData | undefined;
}

export default function WardDetail({ ward, riskData }: WardDetailProps) {
  const [explanation, setExplanation] = useState<RiskExplanation | null>(null);
  const [, setLoading] = useState(false);
  const [activeHazard, setActiveHazard] = useState<'flood' | 'heat'>('flood');

  useEffect(() => {
    if (ward && riskData) {
      fetchExplanation(activeHazard);
    }
  }, [ward, riskData, activeHazard]);

  const fetchExplanation = async (hazard: 'flood' | 'heat') => {
    if (!ward) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/explain/${ward.ward_id}?hazard=${hazard}`);
      if (res.ok) {
        const data = await res.json();
        setExplanation(data);
      }
    } catch (error) {
      console.error('Error fetching explanation:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!ward) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8">
        <MapPin className="w-16 h-16 mb-4 opacity-30" />
        <p className="text-lg font-medium">Select a ward to view details</p>
        <p className="text-sm mt-2">Click on a ward in the list or map</p>
      </div>
    );
  }

  const floodRisk = riskData?.flood;
  const heatRisk = riskData?.heat;
  const activeRisk = activeHazard === 'flood' ? floodRisk : heatRisk;

  return (
    <div className="space-y-4">
      {/* Ward Header */}
      <div className="border-2 border-black p-4">
        <div className="flex items-start justify-between">
          <div>
            <Badge variant="outline" className="rounded-none border-black font-mono mb-2">
              {ward.ward_id}
            </Badge>
            <h2 className="text-xl font-black">{ward.ward_name}</h2>
            {ward.ward_name_marathi && (
              <p className="text-sm text-gray-500">{ward.ward_name_marathi}</p>
            )}
          </div>
          <div className="text-right">
            <div 
              className="text-3xl font-black px-3 py-1"
              style={{ 
                backgroundColor: getRiskColor(riskData?.top_risk_score || 0),
                color: (riskData?.top_risk_score || 0) > 60 ? 'white' : 'black'
              }}
            >
              {riskData?.top_risk_score?.toFixed(0) || '-'}
            </div>
            <p className="text-xs font-bold uppercase mt-1">
              {getRiskCategory(riskData?.top_risk_score || 0)} Risk
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-2 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">Pop:</span>
            <span className="font-bold">{ward.population?.toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">Area:</span>
            <span className="font-bold">{ward.area_sqkm?.toFixed(1)} km²</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">Density:</span>
            <span className="font-bold">{ward.population_density?.toFixed(0)}/km²</span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">Elev:</span>
            <span className="font-bold">{ward.elevation_m?.toFixed(0)}m</span>
          </div>
        </div>
      </div>

      {/* Hazard Tabs */}
      <div className="flex gap-2">
        <Button
          variant={activeHazard === 'flood' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveHazard('flood')}
          className={`flex-1 rounded-none font-bold ${
            activeHazard === 'flood' ? 'bg-blue-600' : 'border-blue-600 text-blue-600'
          }`}
        >
          <Droplets className="w-4 h-4 mr-1" />
          Flood
          {floodRisk && (
            <span className="ml-2 px-1.5 py-0.5 bg-white/20 text-xs">
              {floodRisk.event?.toFixed(0)}%
            </span>
          )}
        </Button>
        <Button
          variant={activeHazard === 'heat' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveHazard('heat')}
          className={`flex-1 rounded-none font-bold ${
            activeHazard === 'heat' ? 'bg-orange-600' : 'border-orange-600 text-orange-600'
          }`}
        >
          <Thermometer className="w-4 h-4 mr-1" />
          Heat
          {heatRisk && (
            <span className="ml-2 px-1.5 py-0.5 bg-white/20 text-xs">
              {heatRisk.event?.toFixed(0)}%
            </span>
          )}
        </Button>
      </div>

      {/* Risk Comparison */}
      {activeRisk && (
        <div className="border-2 border-black p-4">
          <h3 className="font-bold text-sm uppercase mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Risk Comparison
          </h3>
          
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Baseline</span>
                <span className="font-mono font-bold">{activeRisk.baseline?.toFixed(1)}%</span>
              </div>
              <div className="h-3 bg-gray-200 overflow-hidden">
                <div 
                  className="h-full bg-gray-500 transition-all"
                  style={{ width: `${activeRisk.baseline}%` }}
                />
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Event (Current)</span>
                <span className="font-mono font-bold">{activeRisk.event?.toFixed(1)}%</span>
              </div>
              <div className="h-3 bg-gray-200 overflow-hidden">
                <div 
                  className={`h-full transition-all ${
                    activeHazard === 'flood' ? 'bg-blue-500' : 'bg-orange-500'
                  }`}
                  style={{ width: `${activeRisk.event}%` }}
                />
              </div>
            </div>
            
            <div className="flex items-center justify-between pt-2 border-t">
              <span className="text-sm text-gray-600">Delta</span>
              <div className="flex items-center gap-2">
                <TrendingUp className={`w-4 h-4 ${
                  activeRisk.delta > 0 ? 'text-red-500' : 'text-green-500'
                }`} />
                <span className={`font-mono font-bold ${
                  activeRisk.delta > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {activeRisk.delta > 0 ? '+' : ''}{activeRisk.delta?.toFixed(1)}%
                </span>
                <span className="text-xs text-gray-500">
                  ({activeRisk.delta_pct?.toFixed(0)}%)
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Explanation */}
      {explanation && (
        <div className="border-2 border-black p-4">
          <h3 className="font-bold text-sm uppercase mb-3 flex items-center gap-2">
            <Info className="w-4 h-4" />
            Risk Explanation
          </h3>
          
          {explanation.surge_level !== 'normal' && (
            <div className={`p-3 mb-3 ${
              explanation.surge_level === 'critical' 
                ? 'bg-red-100 border-red-500' 
                : 'bg-yellow-100 border-yellow-500'
            } border-2`}>
              <div className="flex items-center gap-2">
                <AlertTriangle className={`w-5 h-5 ${
                  explanation.surge_level === 'critical' ? 'text-red-600' : 'text-yellow-600'
                }`} />
                <span className={`font-bold ${
                  explanation.surge_level === 'critical' ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {explanation.surge_description}
                </span>
              </div>
            </div>
          )}
          
          <p className="text-sm mb-4">{explanation.narrative}</p>
          
          {explanation.top_drivers_event?.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">
                Top Contributing Factors
              </h4>
              <div className="space-y-2">
                {explanation.top_drivers_event.slice(0, 3).map((factor, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="w-5 h-5 bg-black text-white text-xs flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <div className="flex justify-between text-sm">
                        <span>{factor.factor}</span>
                        <span className="font-mono">{factor.contribution?.toFixed(1)}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 overflow-hidden">
                        <div 
                          className="h-full bg-black transition-all"
                          style={{ width: `${factor.contribution}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendations */}
      {explanation?.recommendations && explanation.recommendations.length > 0 && (
        <div className="border-2 border-black p-4 bg-yellow-50">
          <h3 className="font-bold text-sm uppercase mb-3">Recommendations</h3>
          <ul className="space-y-2">
            {explanation.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className="w-5 h-5 bg-black text-white text-xs flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
