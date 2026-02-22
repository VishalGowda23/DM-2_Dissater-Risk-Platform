import { useMemo } from 'react';
import { AlertTriangle, Droplets, Thermometer } from 'lucide-react';
import { type RiskData, type Ward, getRiskColor } from '../lib/types';
import { useLang, wardName, hazardKey } from '@/lib/i18n';

interface WardListProps {
  riskData: RiskData[];
  wards: Ward[];
  selectedWard: Ward | null;
  onSelectWard: (ward: Ward) => void;
}

export default function WardList({ riskData, wards, selectedWard, onSelectWard }: WardListProps) {
  const { t, lang } = useLang();
  // Merge ward data with risk data and sort by risk
  const mergedData = useMemo(() => {
    const wardMap: { [key: string]: Ward } = {};
    wards.forEach(w => wardMap[w.ward_id] = w);
    
    return riskData
      .map(risk => ({
        risk,
        ward: wardMap[risk.ward_id]
      }))
      .filter(item => item.ward)
      .sort((a, b) => (b.risk.top_risk_score || 0) - (a.risk.top_risk_score || 0));
  }, [riskData, wards]);

  const getHazardIcon = (hazard: string) => {
    switch (hazard) {
      case 'flood':
        return <Droplets className="w-4 h-4 text-blue-500" />;
      case 'heat':
        return <Thermometer className="w-4 h-4 text-orange-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="divide-y divide-gray-200">
      {mergedData.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="font-medium">{t('noRiskData')}</p>
          <p className="text-sm mt-1">{t('clickCalculate')}</p>
        </div>
      ) : (
        mergedData.map(({ risk, ward }) => {
          const isSelected = selectedWard?.ward_id === ward.ward_id;
          const riskScore = risk.top_risk_score || 0;
          const riskColor = getRiskColor(riskScore);
          
          return (
            <div
              key={ward.ward_id}
              onClick={() => onSelectWard(ward)}
              className={`
                p-3 cursor-pointer transition-all
                ${isSelected ? 'bg-gray-100 border-l-4 border-black' : 'hover:bg-gray-50 border-l-4 border-transparent'}
              `}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-500">{ward.ward_id}</span>
                    <h3 className="font-bold text-sm truncate">{wardName(ward, lang)}</h3>
                  </div>
                  
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
                    <span>{t('popLabel')} {(ward.population / 1000).toFixed(1)}k</span>
                    {risk.flood && risk.flood.delta > 10 && (
                      <span className="text-red-600 font-bold">
                        +{risk.flood.delta.toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-1">
                  <div 
                    className="px-2 py-1 font-black text-sm"
                    style={{ 
                      backgroundColor: riskColor,
                      color: riskScore > 60 ? 'white' : 'black'
                    }}
                  >
                    {riskScore.toFixed(0)}%
                  </div>
                  <div className="flex items-center gap-1">
                    {getHazardIcon(risk.top_hazard)}
                    <span className="text-xs font-medium uppercase">{t(hazardKey(risk.top_hazard))}</span>
                  </div>
                </div>
              </div>
              
              {/* Risk bars */}
              <div className="mt-2 space-y-1">
                {risk.flood && (
                  <div className="flex items-center gap-2">
                    <Droplets className="w-3 h-3 text-blue-500" />
                    <div className="flex-1 h-2 bg-gray-200 overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 transition-all"
                        style={{ width: `${risk.flood.event}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono w-8 text-right">
                      {risk.flood.event?.toFixed(0)}%
                    </span>
                  </div>
                )}
                {risk.heat && (
                  <div className="flex items-center gap-2">
                    <Thermometer className="w-3 h-3 text-orange-500" />
                    <div className="flex-1 h-2 bg-gray-200 overflow-hidden">
                      <div 
                        className="h-full bg-orange-500 transition-all"
                        style={{ width: `${risk.heat.event}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono w-8 text-right">
                      {risk.heat.event?.toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
