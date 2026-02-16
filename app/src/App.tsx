import { useState, useEffect } from 'react';
import { AlertTriangle, Droplets, Activity, Map as MapIcon, BarChart3, Settings } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';

import RiskMap from './components/RiskMap';
import WardList from './components/WardList';
import WardDetail from './components/WardDetail';
import RiskSummary from './components/RiskSummary';
import ResourceOptimizer from './components/ResourceOptimizer';
import ScenarioSimulator from './components/ScenarioSimulator';
import { API_BASE_URL, type Ward, type RiskData } from './lib/types';
import './App.css';

function App() {
  const [selectedWard, setSelectedWard] = useState<Ward | null>(null);
  const [riskData, setRiskData] = useState<RiskData[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [activeTab, setActiveTab] = useState('map');

  // Fetch wards and risk data
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch wards
      const wardsRes = await fetch(`${API_BASE_URL}/api/wards`);
      const wardsData = await wardsRes.json();
      setWards(wardsData.wards);
      
      // Fetch risk data
      const riskRes = await fetch(`${API_BASE_URL}/api/risk`);
      const riskJson = await riskRes.json();
      setRiskData(riskJson.risk_data);
      setLastUpdated(riskJson.timestamp);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to fetch data from server');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchData();
    toast.success('Data refreshed');
  };

  const handleTriggerIngestion = async () => {
    try {
      toast.info('Starting weather data ingestion...');
      const res = await fetch(`${API_BASE_URL}/api/ingest/weather`, {
        method: 'POST'
      });
      const data = await res.json();
      toast.success(`Ingestion complete: ${data.successful}/${data.total_wards} wards`);
      fetchData();
    } catch (error) {
      toast.error('Ingestion failed');
    }
  };

  const handleCalculateRisks = async () => {
    try {
      toast.info('Calculating risk scores...');
      const res = await fetch(`${API_BASE_URL}/api/calculate-risks`, {
        method: 'POST'
      });
      const data = await res.json();
      toast.success(`Calculated risks for ${data.processed} wards`);
      fetchData();
    } catch (error) {
      toast.error('Risk calculation failed');
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f0] text-gray-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b-4 border-black sticky top-0 z-50">
        <div className="max-w-[1920px] mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-black text-white p-2 rounded-none">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-black tracking-tight uppercase">
                  DisasterIQ
                </h1>
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Pune Intelligence Platform
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="font-medium">LIVE</span>
                {lastUpdated && (
                  <span className="text-gray-500">
                    Updated: {new Date(lastUpdated).toLocaleTimeString()}
                  </span>
                )}
              </div>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleRefresh}
                  className="border-2 border-black rounded-none font-bold hover:bg-black hover:text-white"
                >
                  Refresh
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleTriggerIngestion}
                  className="border-2 border-black rounded-none font-bold hover:bg-black hover:text-white"
                >
                  <Droplets className="w-4 h-4 mr-1" />
                  Ingest
                </Button>
                <Button 
                  variant="default" 
                  size="sm"
                  onClick={handleCalculateRisks}
                  className="bg-black text-white rounded-none font-bold hover:bg-gray-800"
                >
                  <Activity className="w-4 h-4 mr-1" />
                  Calculate
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1920px] mx-auto p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="bg-white border-2 border-black rounded-none p-1 gap-1">
            <TabsTrigger 
              value="map" 
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold"
            >
              <MapIcon className="w-4 h-4 mr-2" />
              Risk Map
            </TabsTrigger>
            <TabsTrigger 
              value="summary"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Summary
            </TabsTrigger>
            <TabsTrigger 
              value="optimizer"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold"
            >
              <Settings className="w-4 h-4 mr-2" />
              Optimizer
            </TabsTrigger>
            <TabsTrigger 
              value="scenarios"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold"
            >
              <Activity className="w-4 h-4 mr-2" />
              Scenarios
            </TabsTrigger>
          </TabsList>

          <TabsContent value="map" className="mt-0">
            <div className="grid grid-cols-12 gap-4 h-[calc(100vh-180px)]">
              {/* Left Panel - Ward List */}
              <div className="col-span-3 bg-white border-2 border-black overflow-hidden flex flex-col">
                <div className="p-3 bg-black text-white">
                  <h2 className="font-black uppercase tracking-wider">Ward Rankings</h2>
                </div>
                <div className="flex-1 overflow-auto">
                  <WardList 
                    riskData={riskData} 
                    wards={wards}
                    selectedWard={selectedWard}
                    onSelectWard={setSelectedWard}
                  />
                </div>
              </div>

              {/* Center Panel - Map */}
              <div className="col-span-6 bg-white border-2 border-black overflow-hidden">
                <RiskMap 
                  riskData={riskData}
                  wards={wards}
                  selectedWard={selectedWard}
                  onSelectWard={setSelectedWard}
                />
              </div>

              {/* Right Panel - Ward Detail */}
              <div className="col-span-3 bg-white border-2 border-black overflow-hidden flex flex-col">
                <div className="p-3 bg-black text-white">
                  <h2 className="font-black uppercase tracking-wider">Ward Details</h2>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  <WardDetail 
                    ward={selectedWard}
                    riskData={riskData.find(r => r.ward_id === selectedWard?.ward_id)}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="summary" className="mt-0">
            <RiskSummary riskData={riskData} wards={wards} />
          </TabsContent>

          <TabsContent value="optimizer" className="mt-0">
            <ResourceOptimizer riskData={riskData} wards={wards} />
          </TabsContent>

          <TabsContent value="scenarios" className="mt-0">
            <ScenarioSimulator riskData={riskData} wards={wards} />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t-2 border-black mt-auto">
        <div className="max-w-[1920px] mx-auto px-4 py-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="font-medium">Data Sources:</span>
              <span>Open-Meteo API</span>
              <span>•</span>
              <span>PMC Ward Data</span>
              <span>•</span>
              <span>Census 2011</span>
            </div>
            <div>
              <span>© 2024 Disaster Intelligence Platform</span>
            </div>
          </div>
        </div>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;
