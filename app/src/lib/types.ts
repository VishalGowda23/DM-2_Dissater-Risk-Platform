// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Ward Types
export interface Ward {
  id: number;
  ward_id: string;
  ward_name: string;
  ward_name_marathi?: string;
  centroid: {
    lat: number;
    lon: number;
  };
  population: number;
  population_density?: number;
  elderly_ratio?: number;
  area_sqkm?: number;
  elevation_m?: number;
  drainage_index?: number;
  impervious_surface_pct?: number;
  historical_flood_count_10y?: number;
  historical_heatwave_days_10y?: number;
  baseline_flood_risk?: number;
  baseline_heat_risk?: number;
}

// Risk Types
export interface HazardRisk {
  baseline: number;
  event: number;
  delta: number;
  delta_pct: number;
}

export interface RiskData {
  ward_id: string;
  ward_name: string;
  population: number;
  centroid: {
    lat: number;
    lon: number;
  };
  flood?: HazardRisk;
  heat?: HazardRisk;
  top_hazard: string;
  top_risk_score: number;
}

// Resource Types
export interface ResourceAllocation {
  allocated: number;
  need_score: number;
  proportion: number;
  is_critical: boolean;
}

export interface WardAllocation {
  ward_id: string;
  ward_name: string;
  population: number;
  risk: {
    flood: number;
    heat: number;
    delta: number;
  };
  need_score: number;
  resources: {
    [key: string]: ResourceAllocation;
  };
}

export interface OptimizationResult {
  timestamp: string;
  scenario: {
    use_delta: boolean;
  };
  total_resources: {
    [key: string]: number;
  };
  total_allocated: {
    [key: string]: number;
  };
  ward_allocations: WardAllocation[];
  explanations: {
    [key: string]: string;
  };
  summary: {
    total_wards: number;
    critical_wards: number;
    highest_need_ward: string;
  };
}

// Scenario Types
export interface ScenarioParams {
  name: string;
  rainfall_multiplier: number;
  temp_anomaly_addition: number;
  drainage_efficiency_multiplier: number;
  population_growth_pct: number;
  forecast_hours: number;
}

export interface ScenarioResult {
  scenario: ScenarioParams;
  comparison?: {
    baseline: RiskData[];
    scenario: RiskData[];
  };
  aggregate_impact?: {
    avg_flood_risk_change: number;
    avg_heat_risk_change: number;
    wards_newly_critical: number;
    total_wards: number;
  };
  results?: {
    baseline: RiskData;
    scenario: RiskData;
  }[];
  timestamp: string;
}

// Explanation Types
export interface RiskFactor {
  factor: string;
  contribution: number;
  value: number;
  weight: number;
}

export interface RiskExplanation {
  ward_id: string;
  ward_name: string;
  hazard: string;
  baseline_risk: number;
  event_risk: number;
  delta: number;
  delta_pct: number;
  surge_level: string;
  surge_description: string;
  top_drivers_event: RiskFactor[];
  top_drivers_baseline: RiskFactor[];
  narrative: string;
  recommendations: string[];
}

// Summary Types
export interface RiskSummary {
  timestamp: string;
  city: string;
  total_wards: number;
  total_population: number;
  average_risks: {
    flood: number;
    heat: number;
  };
  critical_wards: {
    count: number;
    wards: {
      ward_id: string;
      hazard: string;
      risk: number;
    }[];
  };
  high_risk_wards: {
    count: number;
    wards: {
      ward_id: string;
      hazard: string;
      risk: number;
    }[];
  };
  overall_status: string;
}

// Helper functions
export function getRiskColor(risk: number): string {
  if (risk <= 30) return '#22c55e'; // Green
  if (risk <= 60) return '#eab308'; // Yellow
  if (risk <= 80) return '#f97316'; // Orange
  return '#ef4444'; // Red
}

export function getRiskCategory(risk: number): string {
  if (risk <= 30) return 'Low';
  if (risk <= 60) return 'Moderate';
  if (risk <= 80) return 'High';
  return 'Critical';
}

export function getRiskBgColor(risk: number): string {
  if (risk <= 30) return 'bg-green-100 border-green-500';
  if (risk <= 60) return 'bg-yellow-100 border-yellow-500';
  if (risk <= 80) return 'bg-orange-100 border-orange-500';
  return 'bg-red-100 border-red-500';
}
