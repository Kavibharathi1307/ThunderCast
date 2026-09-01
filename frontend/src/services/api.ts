import axios from 'axios'
import { API_URL } from '../lib/config'
import type {
  AlertListResponse,
  ForecastResponse,
  HealthResponse,
  HistoricalEventListResponse,
  HistoricalAnalyticsResponse,
  ImpactResponse,
  ModelAnalyticsResponse,
  NowcastResponse,
  RiskGridResponseWrapper,
  RiskResponseWrapper,
  StormCellListResponse,
  StormPredictionResponse,
  StormTrackListResponse,
  ExplanationResponse,
  WeatherResponse,
} from '../types/api'

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/api/health')
  return data
}

export async function getCurrentWeather(
  latitude: number,
  longitude: number,
): Promise<WeatherResponse> {
  const { data } = await apiClient.get<WeatherResponse>('/api/weather/current', {
    params: { latitude, longitude },
  })
  return data
}

export async function getForecast(
  latitude: number,
  longitude: number,
): Promise<ForecastResponse> {
  const { data } = await apiClient.get<ForecastResponse>(
    `/api/forecast/${latitude}/${longitude}`,
  )
  return data
}

export async function getRisk(
  latitude: number,
  longitude: number,
): Promise<RiskResponseWrapper> {
  const { data } = await apiClient.get<RiskResponseWrapper>(
    `/api/risk/${latitude}/${longitude}`,
  )
  return data
}

export async function getAlerts(): Promise<AlertListResponse> {
  const { data } = await apiClient.get<AlertListResponse>('/api/alerts')
  return data
}

export async function getHistoricalEvents(): Promise<HistoricalEventListResponse> {
  const { data } = await apiClient.get<HistoricalEventListResponse>(
    '/api/historical',
  )
  return data
}

export async function getHistoricalAnalytics(): Promise<HistoricalAnalyticsResponse> {
  const { data } = await apiClient.get<HistoricalAnalyticsResponse>(
    '/api/historical/analytics',
  )
  return data
}

export async function getRiskGrid(
  latitude?: number,
  longitude?: number,
): Promise<RiskGridResponseWrapper> {
  const { data } = await apiClient.get<RiskGridResponseWrapper>(
    '/api/map/risk-grid',
    latitude != null && longitude != null
      ? { params: { latitude, longitude } }
      : undefined,
  )
  return data
}

export async function getStormCells(): Promise<StormCellListResponse> {
  const { data } = await apiClient.get<StormCellListResponse>(
    '/api/storm/cells',
  )
  return data
}

export async function getStormTracks(): Promise<StormTrackListResponse> {
  const { data } = await apiClient.get<StormTrackListResponse>(
    '/api/storm/tracks',
  )
  return data
}

export async function getNowcast(
  latitude: number,
  longitude: number,
): Promise<NowcastResponse> {
  const { data } = await apiClient.get<NowcastResponse>('/api/nowcast', {
    params: { latitude, longitude },
  })
  return data
}

export async function getImpact(
  latitude: number,
  longitude: number,
): Promise<ImpactResponse> {
  const { data } = await apiClient.get<ImpactResponse>('/api/impact', {
    params: { latitude, longitude },
  })
  return data
}

export async function getStormPredictions(): Promise<StormPredictionResponse> {
  const { data } = await apiClient.get<StormPredictionResponse>(
    '/api/storms/predictions',
  )
  return data
}

export async function getExplanation(
  latitude: number,
  longitude: number,
): Promise<ExplanationResponse> {
  const { data } = await apiClient.get<ExplanationResponse>(
    `/api/explainability/${latitude}/${longitude}`,
  )
  return data
}

export async function getModelAnalytics(): Promise<ModelAnalyticsResponse> {
  const { data } = await apiClient.get<ModelAnalyticsResponse>(
    '/api/analytics/model',
  )
  return data
}

export { API_URL }
