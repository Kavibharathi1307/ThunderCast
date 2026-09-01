import { useState } from 'react'
import { getImpact, getNowcast } from '../services/api'
import type { LocationPoint, NowcastPoint } from '../types/api'
import { useAsync } from '../hooks/useAsync'
import LocationSelector, {
  DEFAULT_LOCATION,
} from '../components/common/LocationSelector'
import Panel from '../components/common/Panel'
import ForecastChart from '../components/forecast/ForecastChart'
import ForecastTimeline from '../components/forecast/ForecastTimeline'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import EnvironmentModeIndicator from '../components/common/EnvironmentModeIndicator'
import MetricIndicator from '../components/common/MetricIndicator'
import ImpactPanel from '../components/risk/ImpactPanel'

const IMPACT_CATEGORIES = [
  'flooding',
  'roads',
  'agriculture',
  'waterlogging',
  'lightning',
  'hail',
  'visibility',
] as const

const mapToForecastPoint = (p: NowcastPoint) => ({
  lead_time_hours: p.horizon_hours,
  thunderstorm_probability: p.thunderstorm_probability,
  hail_probability: p.hail_probability,
  cloudburst_probability: p.cloudburst_probability,
  latitude: p.latitude,
  longitude: p.longitude,
  timestamp: p.forecast_time,
  precipitation_mm: null,
  wind_speed_ms: null,
})

export default function Forecast() {
  const [location, setLocation] = useState<LocationPoint>(DEFAULT_LOCATION)
  const state = useAsync(
    () => getNowcast(location.latitude, location.longitude),
    [location],
  )
  const impactState = useAsync(
    () => getImpact(location.latitude, location.longitude),
    [location],
  )

  const nowcast = state.data
  const points = nowcast?.points ?? []
  const overallRisk = nowcast?.peak_risk ?? 'LOW'
  const impacts = impactState.data?.impacts ?? null

  const peakConfidence = points.length > 0
    ? Math.max(...points.map((p) => p.confidence))
    : 0

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Forecast</h1>
          <p className="mt-1 text-sm text-slate-400">
            Probabilistic 0–6 hour nowcast per location.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <EnvironmentModeIndicator
            mode={state.data?.environment_mode}
            provenance={state.data?.data_provenance}
          />
          <DemoModeIndicator demo={state.data?.demo} note={state.data?.demo_note} />
        </div>
      </div>

      <LocationSelector value={location} onChange={setLocation} />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricIndicator
          label="Horizon"
          value="0–6 hr"
          sublabel="Lead time window"
        />
        <MetricIndicator
          label="Location"
          value={location.name}
          sublabel={`${location.latitude.toFixed(2)}, ${location.longitude.toFixed(2)}`}
        />
        <MetricIndicator
          label="Peak Risk"
          value={overallRisk}
          sublabel={nowcast?.peak_hour != null ? `Peaks ~${nowcast.peak_hour}h` : 'Nowcast window'}
        />
        <MetricIndicator
          label="Confidence"
          value={`${Math.round(peakConfidence * 100)}%`}
          sublabel="Peak model confidence"
        />
      </div>

      <Panel
        title="Forecast Timeline"
        subtitle="Probability (%) by lead hour"
        actions={
          <span className="flex flex-wrap items-center gap-2">
            {nowcast?.risk_start_hour != null && nowcast?.risk_end_hour != null && (
              <span className="hidden items-center gap-1.5 rounded-full border border-amber-700 bg-amber-950/40 px-2.5 py-0.5 text-[11px] font-semibold text-amber-300 sm:inline-flex">
                Peak risk: {nowcast.risk_start_hour}–{nowcast.risk_end_hour}h
              </span>
            )}
            {state.data?.model_label ? (
              <span className="rounded-full border border-sky-800 bg-sky-900/30 px-2.5 py-0.5 text-xs text-sky-300">
                {state.data.model_label}
              </span>
            ) : undefined}
          </span>
        }
      >
        {state.status === 'loading' && <LoadingState label="Loading forecast…" />}
        {state.status === 'error' && (
          <ErrorState message={state.error ?? 'Forecast data unavailable'} onRetry={state.load} />
        )}
        {state.status === 'success' && points.length > 0 && (
          <>
            <ForecastTimeline
              points={points.map(mapToForecastPoint)}
              overallRisk={overallRisk}
            />
            <div className="mt-6">
              <ForecastChart
                points={points.map(mapToForecastPoint)}
                overallRisk={overallRisk}
              />
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <MetricIndicator
                label="Peak Thunderstorm"
                value={`${Math.round(Math.max(...points.map((p) => p.thunderstorm_probability)) * 100)}%`}
                sublabel="Max over 0–6 hr"
              />
              <MetricIndicator
                label="Peak Hail"
                value={`${Math.round(Math.max(...points.map((p) => p.hail_probability)) * 100)}%`}
                sublabel="Max over 0–6 hr"
              />
              <MetricIndicator
                label="Peak Cloudburst"
                value={`${Math.round(Math.max(...points.map((p) => p.cloudburst_probability)) * 100)}%`}
                sublabel="Max over 0–6 hr"
              />
            </div>
          </>
        )}
        {state.status === 'success' && points.length === 0 && (
          <p className="py-10 text-center text-sm text-slate-500">
            No forecast points available.
          </p>
        )}
      </Panel>

      <Panel
        title="Impact-Based Risk"
        subtitle="Prototype impact scores (0–1)"
        actions={
          impactState.data?.label ? (
            <span className="rounded-full border border-amber-800 bg-amber-900/30 px-2.5 py-0.5 text-xs text-amber-300">
              {impactState.data.label}
            </span>
          ) : undefined
        }
      >
        {impactState.status === 'loading' && <LoadingState label="Loading impact scores…" />}
        {impactState.status === 'error' && (
          <ErrorState message={impactState.error ?? 'Impact data unavailable'} onRetry={impactState.load} />
        )}
        {impactState.status === 'success' && impacts && (
          <ImpactPanel impacts={impacts} categories={IMPACT_CATEGORIES} />
        )}
      </Panel>
    </div>
  )
}
