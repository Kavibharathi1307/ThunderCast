import { useMemo, useState } from 'react'
import {
  CloudRain,
  CloudHail,
  CloudLightning,
  Wind,
  Droplets,
  MapPin,
  Gauge,
  Timer,
  Cpu,
} from 'lucide-react'
import {
  getAlerts,
  getCurrentWeather,
  getForecast,
  getImpact,
  getRisk,
  getHistoricalAnalytics,
} from '../services/api'
import type { LocationPoint, RiskLevel, ForecastPoint } from '../types/api'
import { useHealth, type HealthState } from '../hooks/useHealth'
import { useAsync } from '../hooks/useAsync'
import { getRiskMeta } from '../lib/riskLevels'
import LocationSelector, {
  DEFAULT_LOCATION,
} from '../components/common/LocationSelector'
import HazardCard from '../components/dashboard/HazardCard'
import RiskIndicator from '../components/risk/RiskIndicator'
import ExplainableAIPanel from '../components/risk/ExplainableAIPanel'
import ImpactPanel from '../components/risk/ImpactPanel'
import ForecastTimeline from '../components/forecast/ForecastTimeline'
import AlertPanel from '../components/alerts/AlertPanel'
import Panel from '../components/common/Panel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import EnvironmentModeIndicator from '../components/common/EnvironmentModeIndicator'
import StatusIndicator from '../components/common/StatusIndicator'
import AIEngineStatus from '../components/common/AIEngineStatus'
import MonthlyActivityTrend from '../components/analytics/MonthlyActivityTrend'
import RiskMapVisualization from '../components/map/RiskMapVisualization'
import StormMapVisualization from '../components/map/StormMapVisualization'

type HazardKey = 'thunderstorm' | 'hail' | 'cloudburst'

const IMPACT_CATEGORIES = [
  'flooding',
  'roads',
  'agriculture',
  'waterlogging',
  'lightning',
  'hail',
  'visibility',
] as const

const HAZARD_CONFIG: { key: HazardKey; title: string; icon: React.ReactNode }[] = [
  { key: 'thunderstorm', title: 'Thunderstorm Risk', icon: <CloudLightning /> },
  { key: 'hail', title: 'Hail Risk', icon: <CloudHail /> },
  { key: 'cloudburst', title: 'Cloudburst Risk', icon: <CloudRain /> },
]

function statusText(health: HealthState): string {
  switch (health) {
    case 'ok':
      return 'Operational'
    case 'down':
      return 'Offline'
    default:
      return 'Checking…'
  }
}

function statusKey(health: HealthState): 'ok' | 'down' | 'checking' {
  return health === 'ok' ? 'ok' : health === 'down' ? 'down' : 'checking'
}

function situationBlurb(level: RiskLevel): string {
  switch (level) {
    case 'EXTREME':
      return 'Severe convective activity is expected. Take protective action'
    case 'HIGH':
      return 'Significant thunderstorm activity is possible'
    case 'MODERATE':
      return 'Thunderstorm activity is possible'
    default:
      return 'Only minimal convective activity is expected'
  }
}

function forecastPeakWindow(points: ForecastPoint[]): string {
  if (!points || points.length === 0) return 'Determining…'
  const riskiest = points.reduce((a, b) => {
    const pa = Math.max(a.thunderstorm_probability, a.hail_probability, a.cloudburst_probability)
    const pb = Math.max(b.thunderstorm_probability, b.hail_probability, b.cloudburst_probability)
    return pb > pa ? b : a
  })
  const peak = Math.max(
    riskiest.thunderstorm_probability,
    riskiest.hail_probability,
    riskiest.cloudburst_probability,
  )
  const hour = riskiest.timestamp
    ? new Date(riskiest.timestamp).toLocaleTimeString(undefined, { hour: 'numeric' })
    : `+${riskiest.lead_time_hours}h`
  return peak >= 0.4 ? `${hour} (peak ${Math.round(peak * 100)}%)` : `${hour} (low activity)`
}

function CondRow({
  label,
  value,
  icon,
}: {
  label: string
  value: string
  icon: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-1.5 text-xs text-slate-400">
        {icon}
        {label}
      </span>
      <span className="font-mono text-sm text-slate-200">{value}</span>
    </div>
  )
}

export default function Dashboard() {
  const health = useHealth()
  const [location, setLocation] = useState<LocationPoint>(DEFAULT_LOCATION)

  const riskState = useAsync(
    () => getRisk(location.latitude, location.longitude),
    [location],
  )
  const forecastState = useAsync(
    () => getForecast(location.latitude, location.longitude),
    [location],
  )
  const alertsState = useAsync(() => getAlerts(), [])
  const weatherState = useAsync(
    () => getCurrentWeather(location.latitude, location.longitude),
    [location],
  )
  const impactState = useAsync(
    () => getImpact(location.latitude, location.longitude),
    [location],
  )
  const analyticsState = useAsync(() => getHistoricalAnalytics(), [])
  const historicalAnalytics = analyticsState.data?.data

  const riskData = riskState.data?.data
  const forecastPoints = forecastState.data?.points ?? []
  const weatherData = weatherState.data?.data
  const impacts = impactState.data?.impacts ?? null
  const demoMode =
    riskState.data?.demo ?? forecastState.data?.demo ?? alertsState.data?.demo

  const overallRisk: RiskLevel = riskData?.overall_risk ?? 'LOW'

  const hazardValues = useMemo(() => {
    if (!riskData) return null
    return {
      thunderstorm: {
        probability: riskData.thunderstorm_probability,
        confidence: riskData.confidence,
        explanation: riskData.explanation,
      },
      hail: {
        probability: riskData.hail_probability,
        confidence: riskData.confidence,
        explanation: riskData.explanation,
      },
      cloudburst: {
        probability: riskData.cloudburst_probability,
        confidence: riskData.confidence,
        explanation: riskData.explanation,
      },
    }
  }, [riskData])

  return (
    <div className="space-y-6">
      {/* Location selector at top — always visible so the user knows WHERE */}
      <LocationSelector value={location} onChange={setLocation} />

      {/* CURRENT CONVECTIVE SITUATION command center */}
      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-sky-950/60 via-slate-900 to-slate-900">
        {/* Section label + system status */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/60 px-6 py-3">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-widest text-sky-400">
              Current Convective Situation
            </h2>
            <p className="text-xs text-slate-500">
              {location.name} · {location.latitude.toFixed(2)}°N, {location.longitude.toFixed(2)}°E
              {' · '}0–6 hr nowcast window
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: getRiskMeta(overallRisk).hex }} />
              System <StatusIndicator status={statusKey(health)} label={statusText(health)} />
            </span>
          </div>
        </div>

        <div className="grid gap-0 lg:grid-cols-5">
          {/* Risk — primary, most visible */}
          <div className="flex flex-col justify-center border-b border-slate-800/60 p-6 lg:border-b-0 lg:border-r">
            {riskState.status === 'loading' && <LoadingState label="Assessing risk…" />}
            {riskState.status === 'error' && (
              <ErrorState
                title="Risk data unavailable"
                message="We couldn't assess the current convective risk for this location."
                onRetry={riskState.load}
              />
            )}
            {riskState.status === 'success' && riskData && (
              <>
                <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
                  Current Risk
                </p>
                <div className="mt-2 flex items-center gap-3">
                  <span
                    className={`text-5xl font-black tracking-tight ${getRiskMeta(overallRisk).textClass}`}
                  >
                    {overallRisk}
                  </span>
                  <RiskIndicator level={overallRisk} />
                </div>
                <p className="mt-3 text-sm leading-relaxed text-slate-400">
                  {situationBlurb(overallRisk)} in {location.name}.
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Model confidence{' '}
                  <span className="font-mono text-slate-300">
                    {Math.round(riskData.confidence * 100)}%
                  </span>
                </p>
              </>
            )}
          </div>

          {/* Weather summary */}
          <div className="border-b border-slate-800/60 p-6 sm:col-span-2 lg:border-b-0 lg:border-r">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
              Live Conditions
            </p>
            <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 lg:grid-cols-1">
              <CondRow
                label="Temperature"
                value={weatherData?.temperature_c != null ? `${weatherData.temperature_c.toFixed(1)}°C` : '—'}
                icon={<CloudLightning className="h-3.5 w-3.5 text-amber-300" aria-hidden="true" />}
              />
              <CondRow
                label="Humidity"
                value={weatherData?.humidity_percent != null ? `${Math.round(weatherData.humidity_percent)}%` : '—'}
                icon={<Droplets className="h-3.5 w-3.5 text-blue-400" aria-hidden="true" />}
              />
              <CondRow
                label="Wind"
                value={weatherData?.wind_speed_ms != null ? `${weatherData.wind_speed_ms.toFixed(1)} m/s${weatherData.wind_direction_deg != null ? ` @ ${Math.round(weatherData.wind_direction_deg)}°` : ''}` : '—'}
                icon={<Wind className="h-3.5 w-3.5 text-sky-400" aria-hidden="true" />}
              />
              <CondRow
                label="Pressure"
                value={weatherData?.pressure_hpa != null ? `${weatherData.pressure_hpa.toFixed(0)} hPa` : '—'}
                icon={<Gauge className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />}
              />
              <CondRow
                label="Precip"
                value={weatherData?.precipitation_mm != null ? `${weatherData.precipitation_mm.toFixed(1)} mm` : '—'}
                icon={<Droplets className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />}
              />
            </div>
          </div>

          {/* Peak risk + expected next */}
          <div className="p-6 sm:col-span-2 lg:col-span-2">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
              Expect Next
            </p>
            <div className="mt-3 space-y-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-slate-500">
                  <Timer className="h-3.5 w-3.5 text-amber-400" aria-hidden="true" />
                  Peak Risk Window
                </p>
                <p className="mt-1 text-base font-bold text-slate-100">
                  {forecastPeakWindow(forecastPoints)}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {HAZARD_CONFIG.map((h) => {
                  const val = hazardValues?.[h.key]
                  if (!val) return null
                  return (
                    <HazardCard
                      key={h.key}
                      title={h.title}
                      icon={h.icon}
                      probability={val.probability}
                      riskLevel={overallRisk}
                      confidence={val.confidence}
                      explanation={val.explanation}
                      compact
                    />
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Environment strip */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-slate-800/60 px-6 py-2.5 text-[11px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <Cpu className="h-3 w-3 text-sky-400" aria-hidden="true" />
            ThunderCast AI · SIH26084 · Convective Nowcasting
          </span>
          <EnvironmentModeIndicator
            mode={riskState.data?.environment_mode ?? forecastState.data?.environment_mode}
            provenance={riskState.data?.data_provenance ?? forecastState.data?.data_provenance}
          />
          <DemoModeIndicator
            demo={demoMode}
            note={riskState.data?.demo_note ?? forecastState.data?.demo_note}
          />
          <span className="ml-auto">0–6 Hour Nowcasting · Thunderstorm, Hail &amp; Cloudburst</span>
        </div>
      </section>

      {/* AI Engine + Explainability */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="AI Engine" subtitle="Honest model report">
          <AIEngineStatus />
        </Panel>

        {riskState.status === 'success' && riskData && (
          <ExplainableAIPanel
            explanation={riskData.explanation}
            riskFactors={riskData.risk_factors ?? []}
            confidence={riskData.confidence}
          />
        )}
      </div>

      {/* Risk Map */}
      <RiskMapPanel location={location} />

      {/* Forecast Timeline */}
      <Panel
        title="Forecast Timeline"
        subtitle="Next 6 hours · probability by lead time"
        actions={
          <DemoModeIndicator
            demo={forecastState.data?.demo}
            note={forecastState.data?.demo_note}
          />
        }
      >
        {forecastState.status === 'loading' && <LoadingState label="Loading forecast…" />}
        {forecastState.status === 'error' && (
          <ErrorState
            title="Unable to load forecast"
            message={
              forecastState.error ??
              'The forecast service is temporarily unavailable.'
            }
            onRetry={forecastState.load}
          />
        )}
        {forecastState.status === 'success' && forecastPoints.length > 0 && (
          <ForecastTimeline points={forecastPoints} overallRisk={overallRisk} />
        )}
        {forecastState.status === 'success' && forecastPoints.length === 0 && (
          <p className="py-10 text-center text-sm text-slate-500">
            No forecast points available.
          </p>
        )}
      </Panel>

      {/* Impact + Alerts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel
          title="Impact-Based Risk"
          subtitle="Expected human / infrastructure impact"
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
            <ErrorState
              title="Unable to load impact data"
              message={
                impactState.error ?? 'The impact service is temporarily unavailable.'
              }
              onRetry={impactState.load}
            />
          )}
          {impactState.status === 'success' && impacts && (
            <ImpactPanel impacts={impacts} categories={IMPACT_CATEGORIES} />
          )}
        </Panel>

        <Panel
          title="Active Weather Alerts"
          subtitle="Impact-based warnings"
          actions={
            <DemoModeIndicator
              demo={alertsState.data?.demo}
              note={alertsState.data?.demo_note}
            />
          }
        >
          {alertsState.status === 'loading' && <LoadingState label="Loading alerts…" />}
          {alertsState.status === 'error' && (
            <ErrorState
              title="Unable to load alerts"
              message={
                alertsState.error ?? 'The alerts service is temporarily unavailable.'
              }
              onRetry={alertsState.load}
            />
          )}
          {alertsState.status === 'success' && (
            <AlertPanel alerts={alertsState.data?.alerts ?? []} />
          )}
        </Panel>
      </div>

      {/* Storm Tracking */}
      <Panel
        title="Storm Tracking"
        subtitle="Current cell position, historic track and projected path"
        actions={<DemoModeIndicator demo={demoMode} />}
      >
        <StormMapVisualization height="h-[460px]" />
      </Panel>

      {/* Monthly Activity Trend */}
      <Panel
        title="Monthly Activity Trend"
        subtitle="Historical convective activity (demo data)"
        actions={
          <DemoModeIndicator
            demo={analyticsState.data?.demo}
            note={analyticsState.data?.demo_note}
          />
        }
      >
        {analyticsState.status === 'loading' && <LoadingState label="Loading monthly trend…" />}
        {analyticsState.status === 'error' && (
          <ErrorState
            title="Unable to load trend data"
            message={analyticsState.error ?? 'Trend data is temporarily unavailable.'}
            onRetry={analyticsState.load}
          />
        )}
        {analyticsState.status === 'success' &&
          historicalAnalytics &&
          historicalAnalytics.monthly_trends.length > 0 && (
            <MonthlyActivityTrend
              trends={historicalAnalytics.monthly_trends}
              peakMonth={historicalAnalytics.peak_activity_month}
              dateRangeStart={historicalAnalytics.date_range_start}
              dateRangeEnd={historicalAnalytics.date_range_end}
            />
          )}
        {analyticsState.status === 'success' &&
          (!historicalAnalytics || historicalAnalytics.monthly_trends.length === 0) && (
            <p className="py-10 text-center text-sm text-slate-500">
              No monthly activity data available.
            </p>
          )}
      </Panel>
    </div>
  )
}

function RiskMapPanel({ location }: { location: LocationPoint }) {
  return (
    <Panel
      title="Convective Risk Map"
      subtitle="Live location-based hazard assessment"
      actions={
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-sky-300">
          <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
          {location.name}
        </span>
      }
    >
      <RiskMapVisualization location={location} height="h-[480px]" />
    </Panel>
  )
}