import { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { type RiskData, type Ward, getRiskColor } from '../lib/types';

interface RiskMapProps {
  riskData: RiskData[];
  wards: Ward[];
  selectedWard: Ward | null;
  onSelectWard: (ward: Ward) => void;
}

// Map center on Pune
const PUNE_CENTER: [number, number] = [18.5204, 73.8567];

// Component to handle map view changes
function MapController({ selectedWard }: { selectedWard: Ward | null }) {
  const map = useMap();
  
  useEffect(() => {
    if (selectedWard) {
      map.setView(
        [selectedWard.centroid.lat, selectedWard.centroid.lon],
        14,
        { animate: true, duration: 0.5 }
      );
    }
  }, [selectedWard, map]);
  
  return null;
}

export default function RiskMap({ riskData, wards, selectedWard, onSelectWard }: RiskMapProps) {
  // Create ward to risk mapping
  const wardRiskMap = useMemo(() => {
    const map: { [key: string]: RiskData } = {};
    riskData.forEach(risk => {
      map[risk.ward_id] = risk;
    });
    return map;
  }, [riskData]);

  // Get marker size based on population
  const getMarkerRadius = (population: number) => {
    const baseRadius = 12;
    const scale = Math.sqrt(population / 50000);
    return Math.max(baseRadius, Math.min(baseRadius * scale, 25));
  };

  return (
    <div className="h-full w-full relative">
      <MapContainer
        center={PUNE_CENTER}
        zoom={12}
        scrollWheelZoom={true}
        className="h-full w-full"
        style={{ background: '#f5f5f0' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapController selectedWard={selectedWard} />
        
        {wards.map((ward) => {
          const risk = wardRiskMap[ward.ward_id];
          const riskScore = risk?.top_risk_score || 0;
          const isSelected = selectedWard?.ward_id === ward.ward_id;
          
          return (
            <CircleMarker
              key={ward.ward_id}
              center={[ward.centroid.lat, ward.centroid.lon]}
              radius={getMarkerRadius(ward.population)}
              fillColor={getRiskColor(riskScore)}
              color={isSelected ? '#000' : '#333'}
              weight={isSelected ? 4 : 2}
              opacity={1}
              fillOpacity={0.7}
              eventHandlers={{
                click: () => onSelectWard(ward),
              }}
            >
              <Popup>
                <div className="p-2 min-w-[200px]">
                  <h3 className="font-bold text-lg border-b-2 border-black pb-1 mb-2">
                    {ward.ward_name}
                  </h3>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Ward ID:</span>
                      <span className="font-mono font-bold">{ward.ward_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Population:</span>
                      <span className="font-bold">{ward.population?.toLocaleString()}</span>
                    </div>
                    {risk && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Top Hazard:</span>
                          <span className="font-bold uppercase">{risk.top_hazard}</span>
                        </div>
                        <div className="flex justify-between items-center mt-2 pt-2 border-t">
                          <span className="text-gray-600">Risk Score:</span>
                          <span 
                            className="font-black text-xl px-2 py-1"
                            style={{ 
                              backgroundColor: getRiskColor(riskScore),
                              color: riskScore > 60 ? 'white' : 'black'
                            }}
                          >
                            {riskScore?.toFixed(0)}%
                          </span>
                        </div>
                        {risk.flood && (
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Flood:</span>
                            <span className="font-mono">{risk.flood.event?.toFixed(0)}%</span>
                          </div>
                        )}
                        {risk.heat && (
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Heat:</span>
                            <span className="font-mono">{risk.heat.event?.toFixed(0)}%</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white border-2 border-black p-3 shadow-lg z-[1000]">
        <h4 className="font-bold text-sm mb-2 uppercase">Risk Level</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#22c55e' }} />
            <span>Low (0-30%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#eab308' }} />
            <span>Moderate (31-60%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#f97316' }} />
            <span>High (61-80%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#ef4444' }} />
            <span>Critical (81-100%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
