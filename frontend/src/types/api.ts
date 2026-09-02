export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME'

export interface HealthResponse {
  status: string
  service: string
  database: string
  docs?: string
  health?: string
}

export interface WeatherObservation {
  latitude: number
  longitude: number
  timestamp: string
  temperature_c: number | null
  humidity_percent: number | null
  wind_speed_ms: number | null
  wind_direction_deg: number | null
  pressure_hpa: number | null
  precipitation_mm: number | null
  source: string | null
}

export interface WeatherResponse {
  demo: boolean
  demo_note: string | null
  environment_mode: 'DEMO' | 'REAL'
  data_provenance: string
  data: WeatherObservation
}

export interface ForecastPoint {
  latitude: number
  longitude: number
  timestamp: string
  lead_time_hours: number
  thunderstorm_probability: number
  hail_probability: number
  cloudburst_probability: number
  precipitation_mm: number | null
  wind_speed_ms: number | null
}

export interface ForecastResponse {
  demo: boolean
  demo_note: string
  latitude: number
  longitude: number
  environment_mode: 'DEMO' | 'REAL'
  data_provenance: string
  points: ForecastPoint[]
}

export interface RiskFactor {
  name: string
  contribution: number
  description: string
}

export interface RiskAssessment {
  latitude: number
  longitude: number
  timestamp: string
  thunderstorm_probability: number
  hail_probability: number
  cloudburst_probability: number
  overall_risk: RiskLevel
  confidence: number
  explanation: string | null
  risk_factors: RiskFactor[]
}

export interface RiskResponse {
  latitude: number
  longitude: number
  timestamp: string
  thunderstorm_probability: number
  hail_probability: number
  cloudburst_probability: number
  overall_risk: RiskLevel
  confidence: number
  explanation: string | null
  risk_factors: RiskFactor[]
  weather: WeatherObservation | null
  forecast: ForecastPoint | null
}

export interface RiskResponseWrapper {
  demo: boolean
  demo_note: string | null
  environment_mode: 'DEMO' | 'REAL'
  data_provenance: string
  data: RiskResponse
}

export interface AlertImpact {
  category: string
  severity_description: string
  affected_population: string | null
  recommended_action: string
}

export interface Alert {
  id: string | null
  title: string
  message: string
  severity: RiskLevel
  area_name: string | null
  area_latitude: number
  area_longitude: number
  area_radius_km: number | null
  issued_at: string
  valid_until: string
  impacts: AlertImpact[]
  source: string
  confidence: number | null
}

export interface AlertListResponse {
  demo: boolean
  demo_note: string
  count: number
  alerts: Alert[]
}

export interface HistoricalEvent {
  id: string | null
  event_type: string
  occurred_at: string
  latitude: number
  longitude: number
  location_name: string | null
  max_thunderstorm_probability: number | null
  max_hail_probability: number | null
  max_cloudburst_probability: number | null
  risk_level: RiskLevel | null
  confidence: number | null
  impact_summary: string | null
  duration_hours: number | null
  damage_reported: boolean
}

export interface HistoricalEventListResponse {
  demo: boolean
  demo_note: string
  count: number
  events: HistoricalEvent[]
}

export interface EventTypeBreakdown {
  thunderstorm: number
  hail: number
  cloudburst: number
}

export interface RiskDistribution {
  low: number
  moderate: number
  high: number
  extreme: number
}

export interface MonthlyTrend {
  month: string
  count: number
}

export interface HistoricalAnalytics {
  total_events: number
  date_range_start: string
  date_range_end: string
  event_types: EventTypeBreakdown
  risk_distribution: RiskDistribution
  avg_confidence: number
  monthly_trends: MonthlyTrend[]
  peak_activity_month: string
  most_affected_region: string
  total_events_analyzed: number
}

export interface HistoricalAnalyticsResponse {
  demo: boolean
  demo_note: string
  data: HistoricalAnalytics
}

export interface RiskGridBounds {
  min_latitude: number
  min_longitude: number
  max_latitude: number
  max_longitude: number
}

export interface RiskGridCell {
  latitude: number
  longitude: number
  thunderstorm_probability: number
  hail_probability: number
  cloudburst_probability: number
  overall_risk: RiskLevel
  confidence: number
}

export interface RiskGridResponse {
  bounds: RiskGridBounds
  resolution_deg: number
  generated_at: string
  cells: RiskGridCell[]
}

export interface RiskGridResponseWrapper {
  demo: boolean
  demo_note: string | null
  environment_mode?: 'DEMO' | 'REAL'
  data_provenance?: string
  data: RiskGridResponse
}

export interface StormCell {
  id: string
  latitude: number
  longitude: number
  intensity: number
  severity: RiskLevel
  radius_km: number
  movement_speed_kmh: number
  movement_direction_deg: number
  timestamp: string
  precipitation_mm_h: number
  echo_top_km: number | null
  vil_kgm2: number | null
}

export interface StormCellListResponse {
  demo: boolean
  demo_note: string
  count: number
  cells: StormCell[]
}

export interface StormCellPosition {
  latitude: number
  longitude: number
  timestamp: string
  intensity: number
}

export interface StormTrack {
  cell_id: string
  positions: StormCellPosition[]
  projected_positions: StormCellPosition[]
}

export interface StormTrackListResponse {
  demo: boolean
  demo_note: string
  count: number
  tracks: StormTrack[]
}

export interface LocationPoint {
  name: string
  latitude: number
  longitude: number
}

// --- Intelligence layer (Phase 8: nowcast / impact / storms / explainability) ---

export interface NowcastPoint {
  latitude: number
  longitude: number
  forecast_time: string
  horizon_hours: number
  thunderstorm_probability: number
  hail_probability: number
  cloudburst_probability: number
  overall_risk: RiskLevel
  confidence: number
  model_label: string
  model_version: string
}

export interface NowcastResponse {
  demo: boolean
  demo_note: string
  latitude: number
  longitude: number
  forecast_time: string
  window_hours: number
  peak_risk: RiskLevel
  peak_hour: number | null
  risk_start_hour: number | null
  risk_end_hour: number | null
  model_label: string
  model_version: string
  environment_mode: 'DEMO' | 'REAL'
  data_provenance: string
  points: NowcastPoint[]
}

export interface ImpactResponse {
  demo: boolean
  demo_note: string
  latitude: number
  longitude: number
  label: string
  impacts: Record<string, number>
}

export interface PredictedPosition {
  latitude: number
  longitude: number
  valid_time: string
  minutes_ahead: number
  intensity: number
}

export interface StormPrediction {
  cell_id: string
  current_latitude: number
  current_longitude: number
  movement_direction_deg: number
  movement_speed_kmh: number
  current_intensity: number
  label: string
  predicted_positions: PredictedPosition[]
}

export interface StormPredictionResponse {
  demo: boolean
  demo_note: string
  count: number
  predictions: StormPrediction[]
  label: string
}

export interface ExplanationDriver {
  factor: string
  role: 'POSITIVE' | 'REDUCING'
  impact: string
  contribution: number
  description: string
}

export interface ExplanationResponse {
  prediction_type: string
  risk_level: RiskLevel
  summary: string
  drivers: ExplanationDriver[]
  positive_drivers: string[]
  reducing_factors: string[]
  confidence: number
  model_label: string
  model_version: string
}

export interface ModelAnalyticsResponse {
  model_label: string
  model_version: string
  model_status: 'UNTRAINED' | 'TRAINED' | 'FAILED' | 'STALE'
  environment_mode: 'DEMO' | 'REAL'
  data_provenance: string
  architecture: string
  model_name: string
  dataset: string | null
  targets: string[]
  unavailable_targets: string[]
  feature_count: number
  features?: string[]
  training_samples: number
  validation_samples: number
  test_samples: number
  metrics: Record<string, Record<string, number>>
  limitations: string | null
  evaluation: {
    status: string
    message: string
    n_samples: number
    available_metrics: string[]
  }
  feature_surface?: {
    name: string
    group: string
    description: string
  }[]
}
