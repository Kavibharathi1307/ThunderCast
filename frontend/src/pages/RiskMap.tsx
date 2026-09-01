import { useMemo } from 'react'
import { Map as MapIcon } from 'lucide-react'
import { getRiskGrid } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import Panel from '../components/common/Panel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import MetricIndicator from '../components/common/MetricIndicator'
import RiskBadge from '../components/risk/RiskBadge'
import LeafletMap from '../components/map/LeafletMap'

const RISK_COLORS: Record<string, string> = {
  LOW: '#10b981',
  MODERATE: '#f59e0b',
  HIGH: '#f97316',
  EXTREME: '#f43f5e',
}

export default function RiskMap() {
  const state = useAsync(() => getRiskGrid(), [])
  const grid = state.data?.data
  const cells = grid?.cells ?? []

  const mapCenter: [number, number] = useMemo(() => {
    if (grid) {
      return [
        (grid.bounds.min_latitude + grid.bounds.max_latitude) / 2,
        (grid.bounds.min_longitude + grid.bounds.max_longitude) / 2,
      ]
    }
    return [20.0, 78.0]
  }, [grid])

  const markers = useMemo(() => {
    return cells.map((cell) => ({
      latitude: cell.latitude,
      longitude: cell.longitude,
      label: `${cell.overall_risk} Risk — Thunder ${Math.round(cell.thunderstorm_probability * 100)}%`,
      color: RISK_COLORS[cell.overall_risk] ?? '#64748b',
      radius: 10 + Math.round(cell.thunderstorm_probability * 10),
    }))
  }, [cells])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Interactive Risk Map</h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time geographic visualization of convective risk across India.
          </p>
        </div>
        <DemoModeIndicator demo={state.data?.demo} note={state.data?.demo_note} />
      </div>

      {/* Interactive map */}
      <section
        className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950"
        aria-label="Interactive risk map"
      >
        <div className="h-[480px] w-full">
          {state.status === 'loading' && (
            <div className="flex h-full items-center justify-center">
              <LoadingState label="Loading risk map…" />
            </div>
          )}
          {state.status === 'error' && (
            <div className="flex h-full items-center justify-center">
              <div className="w-full max-w-md">
                <ErrorState
                  message={state.error ?? 'Risk grid unavailable'}
                  onRetry={state.load}
                />
              </div>
            </div>
          )}
          {state.status === 'success' && (
            <LeafletMap center={mapCenter} zoom={6} markers={markers} />
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 border-t border-slate-800 bg-slate-900/40 px-4 py-2 text-xs">
          <span className="flex items-center gap-1.5 text-slate-400">
            <MapIcon className="h-3.5 w-3.5" aria-hidden="true" />
            Legend:
          </span>
          {(['LOW', 'MODERATE', 'HIGH', 'EXTREME'] as const).map((level) => (
            <span key={level} className="flex items-center gap-1.5">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: RISK_COLORS[level] }}
              />
              <RiskBadge level={level} />
            </span>
          ))}
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
      <Panel title="Risk Cell Distribution" subtitle="Demo risk grid overview">
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
                {new Date(grid.generated_at).toLocaleTimeString()}. Data is
                clearly-labelled demo data.
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
