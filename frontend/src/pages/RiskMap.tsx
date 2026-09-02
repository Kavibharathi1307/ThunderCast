import { getRiskGrid } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import Panel from '../components/common/Panel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import MetricIndicator from '../components/common/MetricIndicator'
import RiskBadge from '../components/risk/RiskBadge'
import RiskMapVisualization from '../components/map/RiskMapVisualization'
import LocationSelector, {
  DEFAULT_LOCATION,
} from '../components/common/LocationSelector'
import { useState } from 'react'

export default function RiskMap() {
  const [location, setLocation] = useState(DEFAULT_LOCATION)
  const state = useAsync(
    () => getRiskGrid(location.latitude, location.longitude),
    [location.latitude, location.longitude],
  )
  const grid = state.data?.data
  const cells = grid?.cells ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Convective Risk Map</h1>
          <p className="mt-1 text-sm text-slate-400">
            Live location-based hazard assessment for convective storms.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!state.data?.demo && (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-emerald-600/50 bg-emerald-950/40 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-emerald-300"
              role="status"
              aria-label="Live weather data"
            >
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
              </span>
              LIVE WEATHER DATA
            </span>
          )}
          <DemoModeIndicator demo={state.data?.demo} note={state.data?.demo_note} />
        </div>
      </div>

      <LocationSelector value={location} onChange={setLocation} demo={state.data?.demo ?? true} />

      {/* Interactive map */}
      <section
        className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950"
        aria-label="Interactive risk map"
      >
        <div className="p-1">
          <RiskMapVisualization location={location} height="h-[520px]" />
        </div>
      </section>

      {/* Grid metadata */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <MetricIndicator
          label="Region Bounds"
          value={
            grid
              ? `${grid.bounds.min_latitude.toFixed(1)}–${grid.bounds.max_latitude.toFixed(1)} N`
              : '—'
          }
          sublabel={
            grid
              ? `${grid.bounds.min_longitude.toFixed(1)}–${grid.bounds.max_longitude.toFixed(1)} E`
              : 'Awaiting data'
          }
        />
        <MetricIndicator
          label="Grid Resolution"
          value={grid ? `${grid.resolution_deg}°` : '—'}
          sublabel="Cell spacing"
        />
        <MetricIndicator
          label="Risk Cells"
          value={cells.length}
          sublabel="Loaded cells"
        />
      </div>

      {/* Risk distribution */}
      <Panel title="Risk Cell Distribution" subtitle="Risk grid overview">
        {state.status === 'loading' && <LoadingState label="Loading…" />}
        {state.status === 'error' && (
          <ErrorState message={state.error ?? 'Risk grid unavailable'} onRetry={state.load} />
        )}
        {state.status === 'success' && cells.length > 0 && (
          <div>
            <RiskDistribution cells={cells} />
            {grid && (
              <p className="mt-4 text-xs text-slate-500">
                Geospatial risk layer rendered from {cells.length} cells. Grid
                generated at{' '}
                {new Date(grid.generated_at).toLocaleTimeString()}.
              </p>
            )}
          </div>
        )}
        {state.status === 'success' && cells.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            No risk cells available.
          </p>
        )}
      </Panel>
    </div>
  )
}

function RiskDistribution({
  cells,
}: {
  cells: { overall_risk: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME' }[]
}) {
  const counts: Record<string, number> = {}
  for (const c of cells) {
    counts[c.overall_risk] = (counts[c.overall_risk] ?? 0) + 1
  }
  const levels: ('LOW' | 'MODERATE' | 'HIGH' | 'EXTREME')[] = [
    'LOW',
    'MODERATE',
    'HIGH',
    'EXTREME',
  ]
  const total = cells.length
  return (
    <div className="flex flex-wrap gap-2">
      {levels.map((lvl) => {
        const count = counts[lvl] ?? 0
        const pct = total > 0 ? Math.round((count / total) * 100) : 0
        return (
          <div
            key={lvl}
            className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2"
          >
            <RiskBadge level={lvl} />
            <span className="font-mono text-sm text-slate-300">{count}</span>
            <span className="text-xs text-slate-600">· {pct}%</span>
          </div>
        )
      })}
    </div>
  )
}
