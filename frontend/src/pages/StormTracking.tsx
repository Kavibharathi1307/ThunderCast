import { Radar, Activity, Navigation } from 'lucide-react'
import { getStormCells, getStormPredictions, getStormTracks } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import type { StormCell, StormPrediction } from '../types/api'
import Panel from '../components/common/Panel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import MetricIndicator from '../components/common/MetricIndicator'
import StormMapVisualization from '../components/map/StormMapVisualization'
import { getRiskMeta } from '../lib/riskLevels'

const SEVERITY_COLORS: Record<string, string> = {
  LOW: '#10b981',
  MODERATE: '#f59e0b',
  HIGH: '#f97316',
  EXTREME: '#f43f5e',
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function StormTracking() {
  const cellsState = useAsync(() => getStormCells(), [])
  const tracksState = useAsync(() => getStormTracks(), [])
  const predictionsState = useAsync(() => getStormPredictions(), [])
  const cells = cellsState.data?.cells ?? []
  const tracks = tracksState.data?.tracks ?? []
  const predictions = predictionsState.data?.predictions ?? []

  const totalActive = cells.filter((c) => c.intensity > 0.4).length
  const extreme = cells.filter((c) => c.severity === 'EXTREME').length
  const highestIntensity = cells.length > 0
    ? Math.max(...cells.map((c) => c.intensity))
    : 0

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Storm Tracking</h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time detection and tracking of convective storm cells.
          </p>
        </div>
        <DemoModeIndicator demo={cellsState.data?.demo} note={cellsState.data?.demo_note} />
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-sky-800/40 bg-sky-950/20 px-4 py-3 text-xs text-sky-200/80">
        <Radar className="h-4 w-4 text-sky-400" aria-hidden="true" />
        DETECT → PREDICT → TRACK → EXPLAIN → WARN
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricIndicator
          label="Tracked Cells"
          value={cells.length}
          sublabel="Active storm cells"
        />
        <MetricIndicator
          label="High Intensity"
          value={totalActive}
          sublabel="Cells > 40% intensity"
        />
        <MetricIndicator
          label="Extreme Cells"
          value={extreme}
          sublabel="Severe risk"
        />
        <MetricIndicator
          label="Peak Intensity"
          value={highestIntensity > 0 ? `${Math.round(highestIntensity * 100)}%` : '—'}
          sublabel="Most intense cell"
        />
      </div>

      {/* Map visualization */}
      <section
        className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950"
        aria-label="Storm tracking map"
      >
        <div className="p-1">
          <StormMapVisualization height="h-[520px]" />
        </div>
      </section>

      {/* Storm cells list */}
      <Panel
        title="Detected Storm Cells"
        subtitle={`${cells.length} cells in current coverage`}
        actions={<DemoModeIndicator demo={cellsState.data?.demo} note={cellsState.data?.demo_note} />}
      >
        {cellsState.status === 'loading' && <LoadingState label="Loading cells…" />}
        {cellsState.status === 'error' && (
          <ErrorState message={cellsState.error ?? 'Storm cell data unavailable'} onRetry={cellsState.load} />
        )}
        {cellsState.status === 'success' && cells.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            No storm cells currently detected.
          </p>
        )}
        {cellsState.status === 'success' && cells.length > 0 && (
          <div className="space-y-3">
            {cells.map((cell) => (
              <StormCellCard key={cell.id} cell={cell} />
            ))}
          </div>
        )}
      </Panel>

      {/* Movement tracks */}
      <Panel
        title="Cell Movement & Evolution"
        subtitle="Historic positions and projected tracks"
        actions={<DemoModeIndicator demo={tracksState.data?.demo} note={tracksState.data?.demo_note} />}
      >
        {tracksState.status === 'loading' && <LoadingState label="Loading tracks…" />}
        {tracksState.status === 'error' && (
          <ErrorState message={tracksState.error ?? 'Track data unavailable'} onRetry={tracksState.load} />
        )}
        {tracksState.status === 'success' && tracks.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            No track data available.
          </p>
        )}
        {tracksState.status === 'success' && tracks.length > 0 && (
          <div className="space-y-4">
            {tracks.map((track) => (
              <div
                key={track.cell_id}
                className="rounded-xl border border-slate-800 bg-slate-950/40 p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-slate-200 flex items-center gap-2">
                    <Activity className="h-4 w-4 text-sky-400" aria-hidden="true" />
                    {track.cell_id}
                  </h4>
                  <span className="text-xs text-slate-500">
                    {track.positions.length} historic · {track.projected_positions.length} projected
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                      Historic Track
                    </h5>
                    <TrackPoints points={track.positions} />
                  </div>
                  <div>
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-violet-400 mb-2">
                      Projected Path
                    </h5>
                    <TrackPoints points={track.projected_positions} projected />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Baseline storm-motion predictions */}
      <Panel
        title="Predicted Storm Paths"
        subtitle="Baseline storm-motion extrapolation (30/60/90/120 min)"
        actions={
          predictionsState.data?.label ? (
            <span className="rounded-full border border-violet-800 bg-violet-900/30 px-2.5 py-0.5 text-xs text-violet-300">
              {predictionsState.data.label}
            </span>
          ) : undefined
        }
      >
        {predictionsState.status === 'loading' && <LoadingState label="Loading predictions…" />}
        {predictionsState.status === 'error' && (
          <ErrorState message={predictionsState.error ?? 'Prediction data unavailable'} onRetry={predictionsState.load} />
        )}
        {predictionsState.status === 'success' && predictions.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">No predictions available.</p>
        )}
        {predictionsState.status === 'success' && predictions.length > 0 && (
          <div className="space-y-3">
            {predictions.map((pred) => (
              <PredictionCard key={pred.cell_id} prediction={pred} />
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}

function PredictionCard({ prediction }: { prediction: StormPrediction }) {
  return (
    <div className="rounded-xl border border-violet-800/40 bg-slate-950/40 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h4 className="flex items-center gap-2 font-semibold text-slate-200">
          <Navigation className="h-4 w-4 text-violet-400" aria-hidden="true" />
          {prediction.cell_id}
        </h4>
        <span className="text-xs text-slate-500">
          {prediction.movement_speed_kmh.toFixed(0)} km/h @{' '}
          {prediction.movement_direction_deg.toFixed(0)}°
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-4">
        {prediction.predicted_positions.map((pos) => (
          <div
            key={pos.minutes_ahead}
            className="rounded-lg border border-slate-800 bg-slate-900/40 p-3"
          >
            <span className="text-xs font-semibold uppercase tracking-wider text-violet-400">
              +{pos.minutes_ahead} min
            </span>
            <p className="mt-1 font-mono text-xs text-slate-300">
              {pos.latitude.toFixed(3)}°, {pos.longitude.toFixed(3)}°
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Intensity {Math.round(pos.intensity * 100)}%
            </p>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-600 italic">
        Constant-velocity baseline extrapolation. Not a trained storm tracker.
      </p>
    </div>
  )
}

function StormCellCard({ cell }: { cell: StormCell }) {
  const meta = getRiskMeta(cell.severity)
  return (
    <div className={`rounded-xl border ${meta.borderClass} bg-slate-900/40 p-4`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <span
            className={`h-3 w-3 rounded-full ${meta.dotClass}`}
            style={{ boxShadow: `0 0 8px ${SEVERITY_COLORS[cell.severity]}` }}
          />
          <h4 className="font-semibold text-slate-200">{cell.id}</h4>
        </div>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.borderClass} ${meta.bgClass} ${meta.textClass}`}
        >
          {meta.label}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <div>
          <span className="text-xs text-slate-500">Intensity</span>
          <p className="font-mono text-slate-200">{Math.round(cell.intensity * 100)}%</p>
        </div>
        <div>
          <span className="text-xs text-slate-500">Position</span>
          <p className="font-mono text-xs text-slate-300">
            {cell.latitude.toFixed(2)}°, {cell.longitude.toFixed(2)}°
          </p>
        </div>
        <div>
          <span className="text-xs text-slate-500">Radius</span>
          <p className="font-mono text-slate-200">{cell.radius_km.toFixed(0)} km</p>
        </div>
        <div>
          <span className="text-xs text-slate-500">Precip Rate</span>
          <p className="font-mono text-slate-200">{cell.precipitation_mm_h.toFixed(1)} mm/h</p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500">
        <span>
          Movement: {cell.movement_speed_kmh.toFixed(0)} km/h @{' '}
          {cell.movement_direction_deg.toFixed(0)}°
        </span>
        {cell.echo_top_km != null && <span>Echo top: {cell.echo_top_km.toFixed(0)} km</span>}
        {cell.vil_kgm2 != null && <span>VIL: {cell.vil_kgm2.toFixed(0)} kg/m²</span>}
        <span>Updated: {formatTime(cell.timestamp)}</span>
      </div>
    </div>
  )
}

function TrackPoints({
  points,
  projected = false,
}: {
  points: { latitude: number; longitude: number; intensity: number }[]
  projected?: boolean
}) {
  return (
    <div className="space-y-1">
      {points.map((p, i) => (
        <div key={i} className="flex items-center justify-between text-xs">
          <span className="font-mono text-slate-400">
            {p.latitude.toFixed(3)}°, {p.longitude.toFixed(3)}°
          </span>
          <span className={projected ? 'text-violet-400' : 'text-slate-500'}>
            {Math.round(p.intensity * 100)}%
          </span>
        </div>
      ))}
    </div>
  )
}
