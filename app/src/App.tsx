import { useState, useEffect } from 'react';
import { AlertTriangle, Droplets, Activity, Map as MapIcon, BarChart3, Settings, Clock, History, Bell, Navigation, Target, LogOut } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { useLang, LangToggle } from './lib/i18n';
import { useAuth } from './lib/auth';
import AuthPage from './components/AuthPage';

import RiskMap from './components/RiskMap';
import WardList from './components/WardList';
import WardDetail from './components/WardDetail';
import RiskSummary from './components/RiskSummary';
import ResourceOptimizer from './components/ResourceOptimizer';
import ScenarioSimulator from './components/ScenarioSimulator';
import ForecastTimeline from './components/ForecastTimeline';
import HistoricalValidation from './components/HistoricalValidation';
import AlertPanel from './components/AlertPanel';
import EvacuationMap from './components/EvacuationMap';
import DecisionSupport from './components/DecisionSupport';
import { API_BASE_URL, type Ward, type RiskData } from './lib/types';


function App() {
  const [selectedWard, setSelectedWard] = useState<Ward | null>(null);
  const [riskData, setRiskData] = useState<RiskData[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [activeTab, setActiveTab] = useState('map');
  const { t } = useLang();
  const { isAuthenticated, user, logout } = useAuth();

  // Fetch wards and risk data
  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 60000); // Refresh every minute
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

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
      toast.error(t('fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchData();
    toast.success(t('dataRefreshed'));
  };

  const handleTriggerIngestion = async () => {
    try {
      toast.info(t('ingestionStarting'));
      const res = await fetch(`${API_BASE_URL}/api/ingest/weather`, {
        method: 'POST'
      });
      const data = await res.json();
      toast.success(`${t('ingestionComplete')}: ${data.successful}/${data.total_wards}`);
      fetchData();
    } catch (error) {
      toast.error(t('ingestionFailed'));
    }
  };

  const handleCalculateRisks = async () => {
    try {
      toast.info(t('calculatingRisks'));
      const res = await fetch(`${API_BASE_URL}/api/calculate-risks`, {
        method: 'POST'
      });
      const data = await res.json();
      toast.success(`${t('risksCalculated')}: ${data.processed}`);
      fetchData();
    } catch (error) {
      toast.error(t('riskCalcFailed'));
    }
  };

  // Show auth page if not logged in
  if (!isAuthenticated) {
    return (
      <>
        <AuthPage />
        <Toaster />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f5f0] text-gray-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b-4 border-black sticky top-0 z-50">
        <div className="max-w-[1920px] mx-auto px-3 sm:px-4 py-2 sm:py-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 sm:gap-4 min-w-0">
              <div className="bg-black text-white p-1.5 sm:p-2 rounded-none shrink-0">
                <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div className="min-w-0">
                <h1 className="text-sm sm:text-xl font-black tracking-tight uppercase truncate">
                  {t('appName')}
                </h1>
                <p className="text-[10px] sm:text-xs font-bold text-gray-500 uppercase tracking-wider hidden sm:block">
                  {t('appSubtitle')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-4 shrink-0">
              <div className="hidden md:flex items-center gap-2 text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="font-medium">{t('live')}</span>
                {lastUpdated && (
                  <span className="text-gray-500">
                    {t('updated')}: {new Date(lastUpdated).toLocaleTimeString()}
                  </span>
                )}
              </div>

              <div className="flex gap-1 sm:gap-2 items-center">
                <LangToggle />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  className="border-2 border-black rounded-none font-bold hover:bg-black hover:text-white px-2 sm:px-3"
                >
                  <Activity className="w-4 h-4 sm:hidden" />
                  <span className="hidden sm:inline">{t('refresh')}</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTriggerIngestion}
                  className="border-2 border-black rounded-none font-bold hover:bg-black hover:text-white px-2 sm:px-3"
                >
                  <Droplets className="w-4 h-4 sm:mr-1" />
                  <span className="hidden sm:inline">{t('ingest')}</span>
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleCalculateRisks}
                  className="bg-black text-white rounded-none font-bold hover:bg-gray-800 px-2 sm:px-3"
                >
                  <Activity className="w-4 h-4 sm:mr-1" />
                  <span className="hidden sm:inline">{t('calculate')}</span>
                </Button>
                <div className="hidden md:flex items-center gap-2 pl-2 border-l-2 border-gray-300 ml-1">
                  <span className="text-xs font-bold text-gray-500 uppercase">{user?.name}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={logout}
                  className="border-2 border-red-600 text-red-600 rounded-none font-bold hover:bg-red-600 hover:text-white px-2 sm:px-3"
                >
                  <LogOut className="w-4 h-4 sm:mr-1" />
                  <span className="hidden sm:inline">Logout</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1920px] mx-auto p-2 sm:p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="bg-white border-2 border-black rounded-none p-1 gap-1 flex overflow-x-auto max-w-full">
            <TabsTrigger
              value="map"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <MapIcon className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabRiskMap')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="summary"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <BarChart3 className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabSummary')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="optimizer"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <Settings className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabOptimizer')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="scenarios"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <Activity className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabScenarios')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="forecast"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <Clock className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabForecast')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="historical"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <History className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabValidation')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="alerts"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <Bell className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabAlerts')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="evacuation"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <Navigation className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabEvacuation')}</span>
            </TabsTrigger>
            <TabsTrigger
              value="command"
              className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white font-bold shrink-0 px-2 sm:px-3"
            >
              <Target className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">{t('tabCommand')}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="map" className="mt-0">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:h-[calc(100vh-180px)]">
              {/* Left Panel - Ward List */}
              <div className="lg:col-span-3 bg-white border-2 border-black overflow-hidden flex flex-col h-[300px] sm:h-[400px] lg:h-auto">
                <div className="p-3 bg-black text-white">
                  <h2 className="font-black uppercase tracking-wider text-sm sm:text-base">{t('wardRankings')}</h2>
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
              <div className="lg:col-span-6 bg-white border-2 border-black overflow-hidden h-[350px] sm:h-[450px] lg:h-auto">
                <RiskMap
                  riskData={riskData}
                  wards={wards}
                  selectedWard={selectedWard}
                  onSelectWard={setSelectedWard}
                />
              </div>

              {/* Right Panel - Ward Detail */}
              <div className="lg:col-span-3 bg-white border-2 border-black overflow-hidden flex flex-col h-[400px] lg:h-auto">
                <div className="p-3 bg-black text-white">
                  <h2 className="font-black uppercase tracking-wider text-sm sm:text-base">{t('wardDetails')}</h2>
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

          <TabsContent value="forecast" className="mt-0">
            <ForecastTimeline riskData={riskData} wards={wards} />
          </TabsContent>

          <TabsContent value="historical" className="mt-0">
            <HistoricalValidation riskData={riskData} wards={wards} />
          </TabsContent>

          <TabsContent value="alerts" className="mt-0">
            <AlertPanel riskData={riskData} wards={wards} />
          </TabsContent>

          <TabsContent value="evacuation" className="mt-0">
            <EvacuationMap riskData={riskData} wards={wards} />
          </TabsContent>

          <TabsContent value="command" className="mt-0">
            <DecisionSupport riskData={riskData} wards={wards} />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t-2 border-black mt-auto">
        <div className="max-w-[1920px] mx-auto px-3 sm:px-4 py-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
              <span className="font-medium">{t('dataSources')}:</span>
              <span>{t('openMeteo')}</span>
              <span>•</span>
              <span>{t('pmcWard')}</span>
              <span>•</span>
              <span>{t('census')}</span>
            </div>
          </div>
        </div>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;
