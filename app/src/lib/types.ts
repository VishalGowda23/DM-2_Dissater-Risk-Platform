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
  area_sq_km?: number;
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
  ward_name_marathi?: string;
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
  ward_name_marathi?: string;
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

export interface ResourceGapDetail {
  resource_name: string;
  unit: string;
  total_available: number;
  total_required: number;
  total_allocated: number;
  total_gap: number;
  coverage_pct: number;
  ward_requirements: {
    ward_id: string;
    ward_name?: string;
    required: number;
    allocated: number;
    gap: number;
  }[];
}

export interface ResourceGapSummary {
  total_required: number;
  total_available: number;
  total_gap: number;
  overall_coverage_pct: number;
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
  resource_gap?: {
    [key: string]: ResourceGapDetail;
  };
  resource_gap_summary?: ResourceGapSummary;
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
  risk_score?: Record<string, unknown>;
  top_drivers?: unknown[];
  shap_values?: Record<string, number>;
  ward_characteristics?: Record<string, number | null>;
  confidence?: number;
  uncertainty?: number;
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

// ─── Forecast Types ─────────────────────────────────────────────────────────
export interface ForecastTimepoint {
  hour: number;
  timestamp: string;
  flood_risk: number;
  heat_risk: number;
  combined_risk: number;
  alert_level: string;
  rainfall_mm: number;
  temperature_c: number;
}

export interface WardForecast {
  ward_id: string;
  ward_name: string;
  ward_name_marathi?: string;
  population: number;
  centroid: { lat: number; lon: number };
  baseline: { flood: number; heat: number };
  timeline: ForecastTimepoint[];
  peak: { risk: number; hour: number; timestamp: string; hazard: string };
  time_to_critical: number | null;
  trend: string;
  current_alert: string;
  max_alert: string;
}

// ─── Historical Types ───────────────────────────────────────────────────────
export interface HistoricalEvent {
  event_id: string;
  name: string;
  date: string;
  end_date: string;
  event_type: string;
  severity: string;
  description: string;
  affected_wards: string[];
  actual_damage: Record<string, number | boolean | string>;
  source: string;
}

export interface WardPrediction {
  ward_id: string;
  ward_name: string;
  ward_name_marathi?: string;
  baseline_risk: number;
  predicted_risk: number;
  actually_affected: boolean;
  model_flagged: boolean;
  classification: string;
  risk_category: string;
}

// ─── River Types ────────────────────────────────────────────────────────────
export interface RiverStation {
  station_id: string;
  name: string;
  river: string;
  lat: number;
  lon: number;
  danger_level_m: number;
  warning_level_m: number;
  normal_level_m: number;
  nearby_wards: string[];
}

// ─── Alert Types ────────────────────────────────────────────────────────────
export interface Alert {
  alert_id: string;
  ward_id: string;
  ward_name: string;
  ward_name_marathi?: string;
  alert_type: string;
  priority: string;
  hazard: string;
  risk_score: number;
  title_en: string;
  message_en: string;
  title_mr: string;
  message_mr: string;
  actions: string[];
  shelter_info: Record<string, unknown> | null;
  timestamp: string;
  channel: string;
  evacuation_route?: {
    recommended_shelter: {
      name: string;
      type: string;
      capacity: number;
      contact: string;
      facilities: string[];
      lat: number;
      lon: number;
      distance_km: number;
      travel_time_min: number;
    } | null;
    route_coords: [number, number][];
    route_safety: { safety_score: number; status: string; avoid_roads: string[]; safe_alternatives: string[] };
    evacuation_urgency: string;
    alternatives: { name: string; distance_km: number; travel_time_min: number; route_coords: [number, number][] }[];
  } | null;
}

// ─── Evacuation Types ───────────────────────────────────────────────────────
export interface Shelter {
  id: string;
  name: string;
  type: string;
  lat: number;
  lon: number;
  capacity: number;
  ward_id: string;
  facilities: string[];
  icon: string;
}

// ─── Decision Support Types ─────────────────────────────────────────────────
export interface ActionItem {
  action_id: string;
  priority: string;
  category: string;
  ward_id: string;
  ward_name: string;
  ward_name_marathi?: string;
  title: string;
  description: string;
  justification: string;
  resources_needed: { type: string; count: number }[];
  estimated_impact: string;
  status: string;
  assigned_to: string;
  deadline: string;
}

