import { useMemo, useState } from 'react'
import {
  Map as MapIcon,
  Crosshair,
  AlertTriangle,
  Maximize2,
  Locate,
  ShieldAlert,
  Clock,
  Navigation,
  Droplets,
  Info,
} from 'lucide-react'
import { getRiskGrid, getRisk, getNowcast } from '../../services/api'
import { useAsync } from '../../hooks/useAsync'
import LoadingState from '../common/LoadingState'
import ErrorState from '../common/ErrorState'
import LeafletMap, { type MapRect } from './LeafletMap'
import type {
  RiskLevel,
  LocationPoint,
  NowcastResponse,
  RiskAssessment,
} from '../../types/api'
import { getRiskMeta, RISK_COLORS } from '../../lib/riskLevels'

interface RiskMapVisualizationProps {
  location?: LocationPoint
  height?: string
}

const LEVELS: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'EXTREME']

function fmtTime(iso?: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function RiskMapVisualization({
  location,
  height = 'h-[480px]',
}: RiskMapVisualizationProps) {
  // Risk grid (centred on the selected location) + location-specific risk +
  // nowcast for the info card.
  const gridState = useAsync(
    () =>
      location
        ? getRiskGrid(location.latitude, location.longitude)
        : getRiskGrid(),
    [location?.latitude, location?.longitude],
  )
  const riskState = useAsync(
    () =>
      location
        ? getRisk(location.latitude, location.longitude)
        : Promise.resolve(null),
    [location],
  )
  const nowcastState = useAsync(
    () =>
      location
        ? getNowcast(location.latitude, location.longitude)
        : Promise.resolve(null),
    [location],
  )
  const [fitToken, setFitToken] = useState(0)

  const grid = gridState.data?.data
  const cells = grid?.cells ?? []
  const riskData: RiskAssessment | null = riskState.data?.data ?? null
  const nowcast: NowcastResponse | null = nowcastState.data ?? null

  const primaryRisk = riskData?.overall_risk ?? nowcast?.peak_risk ?? 'LOW'
  const primaryMeta = getRiskMeta(primaryRisk)

  // Determine primary hazard from the highest probability.
  const primaryHazard = useMemo(() => {
    const r = riskData
    if (!r) return 'Convective'
    const values: { key: string; v: number }[] = [
      { key: 'Thunderstorm', v: r.thunderstorm_probability },
      { key: 'Hail', v: r.hail_probability },
      { key: 'Cloudburst', v: r.cloudburst_probability },
    ]
    values.sort((a, b) => b.v - a.v)
    return values[0].key
  }, [riskData])

  // Rectangle cells tile into a coherent grid (centers at cell lat/lon).
  const rects: MapRect[] = useMemo(() => {
    if (!grid) return []
    const span = Math.max(grid.resolution_deg, 0.0001)
    return cells.map((cell) => ({
      latitude: cell.latitude,
      longitude: cell.longitude,
      spanLat: span,
      spanLng: span,
      color: RISK_COLORS[cell.overall_risk],
      fillOpacity: 0.38,
      label: `<div style="margin-bottom:4px;font-weight:700;font-size:13px;color:#0f172a;">${cell.overall_risk} Risk</div>
        <div style="font-size:11px;color:#334155;">
          Thunderstorm: ${Math.round(cell.thunderstorm_probability * 100)}%<br/>
          Hail: ${Math.round(cell.hail_probability * 100)}%<br/>
          Cloudburst: ${Math.round(cell.cloudburst_probability * 100)}%<br/>
          Confidence: ${Math.round(cell.confidence * 100)}%
        </div>`,
    }))
  }, [grid, cells])

  const selectedLocation = location && {
    latitude: location.latitude,
    longitude: location.longitude,
    label: `Selected Location — ${location.name}`,
  }

  const riskCounts = useMemo(() => {
    const counts: Record<RiskLevel, number> = { LOW: 0, MODERATE: 0, HIGH: 0, EXTREME: 0 }
    cells.forEach((c) => {
      counts[c.overall_risk] = (counts[c.overall_risk] ?? 0) + 1
    })
    return counts
  }, [cells])

  // Frame the map so BOTH the risk grid AND the selected location are visible.
  // This prevents the "where is my location?" disconnect when the selected
  // city sits outside the demo grid region.
  const fitTo = useMemo(() => {
    const gridFit = grid
      ? {
          minLat: grid.bounds.min_latitude,
          minLng: grid.bounds.min_longitude,
          maxLat: grid.bounds.max_latitude,
          maxLng: grid.bounds.max_longitude,
        }
      : undefined
    if (location && gridFit) {
      return {
        minLat: Math.min(gridFit.minLat, location.latitude),
        minLng: Math.min(gridFit.minLng, location.longitude),
        maxLat: Math.max(gridFit.maxLat, location.latitude),
        maxLng: Math.max(gridFit.maxLng, location.longitude),
      }
    }
    return location
      ? {
          minLat: location.latitude,
          minLng: location.longitude,
          maxLat: location.latitude,
          maxLng: location.longitude,
        }
      : gridFit
  }, [grid, location])

  return (
    <div className="grid gap-3 lg:grid-cols-[1fr_280px]">
      {/* Map */}
      <div className={`relative ${height} w-full overflow-hidden rounded-xl border border-slate-800/60`}>
        {gridState.status === 'loading' && (
          <div className="absolute inset-0 z-[400] flex items-center justify-center bg-slate-950/70">
            <LoadingState label="Loading weather intelligence…" />
          </div>
        )}
        {gridState.status === 'error' && (
          <div className="absolute inset-0 z-[400] flex items-center justify-center bg-slate-950/70 px-4">
            <ErrorState
              title="Weather intelligence temporarily unavailable"
              message="We couldn't load the geographic risk layer. The service may be busy."
              onRetry={gridState.load}
            />
          </div>
        )}
        {gridState.status === 'success' &&
          (cells.length > 0 ? (
            <>
              <LeafletMap
                center={[20, 78]}
                zoom={5}
                rects={rects}
                selectedLocation={selectedLocation}
                fitBounds
                fitToken={fitToken}
                fitTo={fitTo}
              />

              {/* Live weather data indicator */}
              {!gridState.data?.demo && (
                <div className="pointer-events-none absolute left-1/2 top-2.5 z-[500] -translate-x-1/2">
                  <span
                    className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/60 bg-slate-950/85 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-300 shadow-lg backdrop-blur"
                    role="status"
                    aria-label="Live weather data"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                    LIVE WEATHER DATA
                  </span>
                </div>
              )}

              {/* Controls */}
              <div className="absolute right-3 top-3 z-[450] flex flex-col gap-1.5">
                <button
                  onClick={() => setFitToken((t) => t + 1)}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-950/85 px-2.5 py-1.5 text-[11px] font-semibold text-slate-300 shadow-lg backdrop-blur transition-colors hover:bg-slate-800 hover:text-sky-300"
                  title="Reset view to the risk region and selected location"
                >
                  <Maximize2 className="h-3 w-3" aria-hidden="true" />
                  Reset view
                </button>
              </div>

              {/* In-map legend */}
              <div className="pointer-events-none absolute bottom-3 left-3 z-[450] rounded-lg border border-slate-700/70 bg-slate-950/90 px-3 py-2 shadow-lg backdrop-blur">
                <p className="mb-1.5 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-slate-400">
                  <MapIcon className="h-3 w-3" aria-hidden="true" /> Risk Level
                </p>
                <div className="flex flex-col gap-1">
                  {LEVELS.map((level) => (
                    <span key={level} className="flex items-center gap-2 text-[10px] text-slate-300">
                      <span
                        className="h-2.5 w-2.5 rounded-sm border border-black/20"
                        style={{
                          backgroundColor: RISK_COLORS[level],
                          boxShadow: `0 0 6px ${RISK_COLORS[level]}66`,
                        }}
                      />
                      {level}
                      <span className="text-slate-500">({riskCounts[level]})</span>
                    </span>
                  ))}
                </div>
                {selectedLocation && (
                  <p className="mt-2 flex items-center gap-1.5 border-t border-slate-700/60 pt-2 text-[10px] font-semibold text-sky-300">
                    <Crosshair className="h-3 w-3" aria-hidden="true" />
                    Selected Location
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 bg-slate-950/50 px-4 text-center text-sm text-slate-500">
              <AlertTriangle className="h-6 w-6 text-slate-600" aria-hidden="true" />
              <span>No risk data is currently available for this location.</span>
            </div>
          )          )}
      </div>

      {/* Side information card */}
      <aside className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Current Risk
          </p>
          <div className="mt-1 flex items-center gap-2">
            <span className={`text-3xl font-black ${primaryMeta.textClass}`}>
              {primaryRisk}
            </span>
            <ShieldAlert className={`h-5 w-5 ${primaryMeta.textClass}`} aria-hidden="true" />
          </div>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">
            {riskData?.explanation ??
              `Convective conditions near ${location?.name ?? 'the selected area'}.`}
          </p>
        </div>

        <dl className="space-y-2.5 border-t border-slate-800/70 pt-3 text-xs">
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-1.5 text-slate-500">
              <Navigation className="h-3 w-3" aria-hidden="true" /> Primary hazard
            </dt>
            <dd className="font-semibold text-slate-200">{primaryHazard}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-1.5 text-slate-500">
              <Clock className="h-3 w-3" aria-hidden="true" /> Peak risk window
            </dt>
            <dd className="font-mono text-slate-200">
              {nowcast?.risk_start_hour != null && nowcast?.risk_end_hour != null
                ? `${nowcast.risk_start_hour}–${nowcast.risk_end_hour}h`
                : '—'}
            </dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-1.5 text-slate-500">
              <Droplets className="h-3 w-3" aria-hidden="true" /> Confidence
            </dt>
            <dd className="font-mono text-slate-200">
              {riskData?.confidence != null
                ? `${Math.round(riskData.confidence * 100)}%`
                : '—'}
            </dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-1.5 text-slate-500">
              <Crosshair className="h-3 w-3" aria-hidden="true" /> Location
            </dt>
            <dd className="text-right text-slate-200">{location?.name ?? '—'}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-1.5 text-slate-500">
              <Info className="h-3 w-3" aria-hidden="true" /> Updated
            </dt>
            <dd className="font-mono text-slate-300">
              {fmtTime(riskData?.timestamp)}
            </dd>
          </div>
        </dl>

        {location && (
          <button
            onClick={() => setFitToken((t) => t + 1)}
            className="mt-auto flex items-center justify-center gap-1.5 rounded-lg border border-sky-700 bg-sky-950/40 px-3 py-2 text-[11px] font-semibold text-sky-300 transition-colors hover:bg-sky-900/40"
            title="Re-center the map on the selected location and risk region"
          >
            <Locate className="h-3.5 w-3.5" aria-hidden="true" />
            Center map on selected location
          </button>
        )}

        <div className="flex items-center justify-between">
          <p className="text-[10px] text-slate-600">
            {grid?.cells.length ?? 0} analysis cells · {grid ? `${grid.resolution_deg}°` : ''} grid
          </p>
          {!gridState.data?.demo && (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-emerald-600/50 bg-emerald-950/40 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-emerald-300"
              role="status"
              aria-label="Live weather data"
            >
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
              </span>
              LIVE
            </span>
          )}
        </div>
      </aside>
    </div>
  )
}
