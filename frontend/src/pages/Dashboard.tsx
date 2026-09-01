import { useMemo, useState } from 'react'
import { CloudRain, CloudHail, CloudLightning, Wind, Droplets } from 'lucide-react'
import { getAlerts, getCurrentWeather, getForecast, getImpact, getRisk } from '../services/api'
import type { LocationPoint, RiskLevel } from '../types/api'
import { useHealth, type HealthState } from '../hooks/useHealth'
import { useAsync } from '../hooks/useAsync'
import LocationSelector, {
  DEFAULT_LOCATION,
} from '../components/common/LocationSelector'
import HazardCard from '../components/dashboard/HazardCard'
import RiskIndicator from '../components/risk/RiskIndicator'
import ExplainableAIPanel from '../components/risk/ExplainableAIPanel'
import ImpactPanel from '../components/risk/ImpactPanel'
import ForecastChart from '../components/forecast/ForecastChart'
import AlertPanel from '../components/alerts/AlertPanel'
import Panel from '../components/common/Panel'
import MetricIndicator from '../components/common/MetricIndicator'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import EnvironmentModeIndicator from '../components/common/EnvironmentModeIndicator'
import StatusIndicator from '../components/common/StatusIndicator'

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
  {
    key: 'thunderstorm',
    title: 'Thunderstorm Risk',
    icon: <CloudLightning />,
  },
  {
    key: 'hail',
    title: 'Hail Risk',
    icon: <CloudHail />,
  },
  {
    key: 'cloudburst',
    title: 'Cloudburst Risk',
    icon: <CloudRain />,
  },
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

  const lastUpdated = riskData?.timestamp

  return (
    <div className="space-y-6">
      {/* Hero */}
      <section className="rounded-2xl border border-slate-800 bg-gradient-to-br from-sky-950/60 via-slate-900 to-slate-900 p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-wider text-sky-400">
              ThunderCast AI · SIH26084
            </p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight md:text-4xl">
              Convective Weather Intelligence
            </h1>
            <p className="mt-2 text-sm font-medium text-slate-400">
              0–6 Hour Nowcasting · Thunderstorm, Hail &amp; Cloudburst
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <EnvironmentModeIndicator
              mode={riskState.data?.environment_mode ?? forecastState.data?.environment_mode}
              provenance={riskState.data?.data_provenance ?? forecastState.data?.data_provenance}
            />
            <DemoModeIndicator
              demo={demoMode}
              note={riskState.data?.demo_note ?? forecastState.data?.demo_note}
            />
          </div>
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            Location:
          </span>
          <span className="rounded-full border border-sky-800 bg-sky-900/30 px-3 py-1 text-sm font-medium text-sky-300">
            {location.name}
          </span>
          <span className="font-mono text-xs text-slate-500">
            {location.latitude.toFixed(2)}°N, {location.longitude.toFixed(2)}°E
          </span>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
          <MetricIndicator
            label="System Status"
            value={<StatusIndicator status={statusKey(health)} label={statusText(health)} />}
            sublabel="Service liveness"
          />
          <MetricIndicator
            label="Data Status"
            value={
              riskState.status === 'success' ? (
                <StatusIndicator status="ok" label="Available" />
              ) : riskState.status === 'error' ? (
                <StatusIndicator status="down" label="Unavailable" />
              ) : (
                <StatusIndicator status="checking" label="Loading…" />
              )
            }
            sublabel="Risk assessment feed"
          />
          <MetricIndicator
            label="Forecast Horizon"
            value="0–6 hr"
            sublabel="Nowcast window"
          />
          <MetricIndicator
            label="Last Updated"
            value={
              lastUpdated
                ? new Date(lastUpdated).toLocaleTimeString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : '—'
            }
            sublabel={lastUpdated ? new Date(lastUpdated).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
            }) : 'Awaiting data'}
          />
          <MetricIndicator
            label="Temperature"
            value={weatherData?.temperature_c != null ? `${weatherData.temperature_c.toFixed(1)}°C` : '—'}
            sublabel={weatherData ? `Feels ${location.name}` : 'Awaiting data'}
          />
          <MetricIndicator
            label="Humidity"
            value={weatherData?.humidity_percent != null ? `${Math.round(weatherData.humidity_percent)}%` : '—'}
            sublabel={weatherData ? 'Relative humidity' : 'Awaiting data'}
          />
        </div>
      </section>

      {/* Live conditions strip */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricIndicator
          label="Wind Speed"
          value={
            <span className="flex items-center gap-1">
              <Wind className="h-4 w-4 text-sky-400" aria-hidden="true" />
              {weatherData?.wind_speed_ms != null ? `${weatherData.wind_speed_ms.toFixed(1)} m/s` : '—'}
            </span>
          }
          sublabel="Current conditions"
        />
        <MetricIndicator
          label="Pressure"
          value={weatherData?.pressure_hpa != null ? `${weatherData.pressure_hpa.toFixed(0)} hPa` : '—'}
          sublabel="Sea-level pressure"
        />
        <MetricIndicator
          label="Precipitation"
          value={
            <span className="flex items-center gap-1">
              <Droplets className="h-4 w-4 text-blue-400" aria-hidden="true" />
              {weatherData?.precipitation_mm != null ? `${weatherData.precipitation_mm.toFixed(1)} mm` : '—'}
            </span>
          }
          sublabel="Current rainfall"
        />
        <MetricIndicator
          label="Data Source"
          value={weatherData?.source ? weatherData.source.toUpperCase() : '—'}
          sublabel="Observation feed"
        />
      </section>

      {/* Location */}
      <LocationSelector value={location} onChange={setLocation} />

      {/* Overall risk */}
      <Panel
        title="Overall Hazard Indicator"
        subtitle="Aggregate convective risk for the selected location"
      >
        {riskState.status === 'loading' && <LoadingState label="Computing risk…" />}
        {riskState.status === 'error' && (
          <ErrorState message={riskState.error ?? 'Risk data unavailable'} onRetry={riskState.load} />
        )}
        {riskState.status === 'success' && riskData && (
          <div className="flex flex-col items-center gap-5">
            <div className="flex items-center gap-4">
              <span className="text-5xl font-black tracking-tight text-slate-100">
                {overallRisk}
              </span>
              <RiskIndicator level={overallRisk} />
            </div>
            <p className="text-sm text-slate-400">
              Confidence:{' '}
              <span className="font-mono text-slate-200">
                {Math.round(riskData.confidence * 100)}%
              </span>
            </p>
          </div>
        )}
      </Panel>

      {/* Hazard cards */}
      <section aria-label="Hazard risk cards">
        {riskState.status === 'loading' && <LoadingState label="Loading hazard risks…" />}
        {riskState.status === 'error' && (
          <ErrorState message={riskState.error ?? 'Hazard data unavailable'} onRetry={riskState.load} />
        )}
        {riskState.status === 'success' && hazardValues && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {HAZARD_CONFIG.map((h) => {
              const val = hazardValues[h.key]
              return (
                <HazardCard
                  key={h.key}
                  title={h.title}
                  icon={h.icon}
                  probability={val.probability}
                  riskLevel={overallRisk}
                  confidence={val.confidence}
                  explanation={val.explanation}
                />
              )
            })}
          </div>
        )}
      </section>

      {/* Explainable AI */}
      {riskState.status === 'success' && riskData && (
        <ExplainableAIPanel
          explanation={riskData.explanation}
          riskFactors={riskData.risk_factors ?? []}
          confidence={riskData.confidence}
        />
      )}

      {/* Impact-based risk */}
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

      {/* Forecast chart */}
      <Panel
        title="0–6 Hour Forecast"
        subtitle="Probability by lead time"
        actions={<DemoModeIndicator demo={forecastState.data?.demo} note={forecastState.data?.demo_note} />}
      >
        {forecastState.status === 'loading' && <LoadingState label="Loading forecast…" />}
        {forecastState.status === 'error' && (
          <ErrorState message={forecastState.error ?? 'Forecast data unavailable'} onRetry={forecastState.load} />
        )}
        {forecastState.status === 'success' && forecastPoints.length > 0 && (
          <ForecastChart points={forecastPoints} overallRisk={overallRisk} />
        )}
        {forecastState.status === 'success' && forecastPoints.length === 0 && (
          <p className="py-10 text-center text-sm text-slate-500">No forecast points available.</p>
        )}
      </Panel>

      {/* Alerts */}
      <Panel
        title="Active Alerts"
        subtitle="Impact-based warnings"
        actions={<DemoModeIndicator demo={alertsState.data?.demo} note={alertsState.data?.demo_note} />}
      >
        {alertsState.status === 'loading' && <LoadingState label="Loading alerts…" />}
        {alertsState.status === 'error' && (
          <ErrorState message={alertsState.error ?? 'Alert data unavailable'} onRetry={alertsState.load} />
        )}
        {alertsState.status === 'success' && (
          <AlertPanel alerts={alertsState.data?.alerts ?? []} />
        )}
      </Panel>
    </div>
  )
}
