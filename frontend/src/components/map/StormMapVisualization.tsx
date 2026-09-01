import { useEffect, useMemo, useState } from 'react'
import type L from 'leaflet'
import { Radar, Navigation, Maximize2, Crosshair, Ship, Clock } from 'lucide-react'
import { getStormCells, getStormTracks } from '../../services/api'
import { useAsync } from '../../hooks/useAsync'
import LoadingState from '../common/LoadingState'
import ErrorState from '../common/ErrorState'
import DemoModeIndicator from '../common/DemoModeIndicator'
import LeafletMap, {
  type MapPolyline,
  type MapCircle,
  createCurrentStormIcon,
  createHistoricalIcon,
  createProjectedIcon,
} from './LeafletMap'
import type { RiskLevel } from '../../types/api'
import { getRiskMeta } from '../../lib/riskLevels'

export const SEVERITY_COLORS: Record<RiskLevel, string> = {
  LOW: '#10b981',
  MODERATE: '#f59e0b',
  HIGH: '#f97316',
  EXTREME: '#f43f5e',
}

// Convert a compass bearing in degrees into a human-readable direction.
function compassDirection(deg: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return dirs[Math.round(((deg % 360) + 360) % 360 / 45) % 8]
}

function timeAgo(iso?: string): string {
  if (!iso) return '—'
  const sec = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (sec < 60) return `${sec}s ago`
  if (sec < 3600) return `${Math.floor(sec / 60)} min ago`
  return `${Math.floor(sec / 3600)} hr ago`
}

interface StormMapVisualizationProps {
  height?: string
}

export default function StormMapVisualization({
  height = 'h-[460px]',
}: StormMapVisualizationProps) {
  const cellsState = useAsync(() => getStormCells(), [])
  const tracksState = useAsync(() => getStormTracks(), [])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [fitToken, setFitToken] = useState(0)

  const cells = cellsState.data?.cells ?? []
  const tracks = tracksState.data?.tracks ?? []

  // Auto-select the most intense storm so an information panel is always shown.
  useEffect(() => {
    if (cells.length > 0 && !cells.some((c) => c.id === selectedId)) {
      const peak = [...cells].sort((a, b) => b.intensity - a.intensity)[0]
      setSelectedId(peak.id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cells])

  const status: 'loading' | 'error' | 'success' =
    cellsState.status === 'loading' || tracksState.status === 'loading'
      ? 'loading'
      : cellsState.status === 'error' || tracksState.status === 'error'
        ? 'error'
        : 'success'

  const error =
    cellsState.error ?? tracksState.error ?? 'Storm data unavailable'

  // Current storm positions (pulsing markers sized by intensity).
  const circles: MapCircle[] = useMemo(
    () =>
      cells.map((cell) => ({
        latitude: cell.latitude,
        longitude: cell.longitude,
        radiusKm: cell.radius_km,
        color: SEVERITY_COLORS[cell.severity],
        fillOpacity: 0.06,
      })),
    [cells],
  )

  const markers = useMemo(() => {
    const mk: {
      latitude: number
      longitude: number
      label: string
      color: string
      radius?: number
      icon?: L.DivIcon
    }[] = []
    cells.forEach((cell) => {
      const isSelected = cell.id === selectedId
      const color = isSelected ? '#f43f5e' : SEVERITY_COLORS[cell.severity]
      mk.push({
        latitude: cell.latitude,
        longitude: cell.longitude,
        color,
        radius: 12 + Math.round(cell.intensity * 14),
        icon: createCurrentStormIcon(color, isSelected),
        label: `<div style="margin-bottom:4px;font-weight:700;font-size:13px;color:#0f172a;">${cell.id}${
          isSelected ? ' — CURRENT' : ''
        }</div>
          <div style="font-size:11px;color:#334155;">
            Severity: ${cell.severity}<br/>
            Intensity: ${Math.round(cell.intensity * 100)}%<br/>
            Radius: ${cell.radius_km.toFixed(0)} km<br/>
            Moving: ${cell.movement_speed_kmh.toFixed(0)} km/h @ ${cell.movement_direction_deg.toFixed(0)}°<br/>
            Precip: ${cell.precipitation_mm_h.toFixed(1)} mm/h
          </div>`,
      })
    })

    return mk
  }, [cells, selectedId])

  // Hist/projected polylines + waypoint dots.
  const { polylines, historyPointMarkers, projectedPointMarkers } = useMemo(() => {
    const lines: MapPolyline[] = []
    const histPoints: {
      latitude: number
      longitude: number
      label: string
      color: string
      radius?: number
      icon?: L.DivIcon
    }[] = []
    const projPoints: {
      latitude: number
      longitude: number
      label: string
      color: string
      radius?: number
      icon?: L.DivIcon
    }[] = []

    tracks.forEach((track) => {
      const cell = cells.find((c) => c.id === track.cell_id)
      const color = cell ? SEVERITY_COLORS[cell.severity] : '#a78bfa'

      if (track.positions.length >= 2) {
        lines.push({
          positions: track.positions,
          color,
          weight: 3,
          label: `${track.cell_id} — historical path`,
          arrows: true,
        })
      }
      // Historic waypoints (darker, filled dots).
      track.positions.forEach((p, i) => {
        const isOrigin = i === 0
        histPoints.push({
          latitude: p.latitude,
          longitude: p.longitude,
          icon: createHistoricalIcon(color),
          color,
          label: `${track.cell_id}${isOrigin ? ' · origin' : ' · historical'} · ${Math.round(p.intensity * 100)}%`,
        })
      })

      if (track.projected_positions.length >= 2) {
        lines.push({
          positions: track.projected_positions,
          color,
          weight: 2.5,
          dashArray: '8 6',
          label: `${track.cell_id} — forecast path`,
          arrows: true,
        })
      }
      track.projected_positions.forEach((p) => {
        projPoints.push({
          latitude: p.latitude,
          longitude: p.longitude,
          icon: createProjectedIcon(color),
          color,
          label: `${track.cell_id} · projected · ${Math.round(p.intensity * 100)}%`,
        })
      })
    })

    return { polylines: lines, historyPointMarkers: histPoints, projectedPointMarkers: projPoints }
  }, [tracks, cells])

  const allMarkers = [
  ...markers,
  ...historyPointMarkers,
  ...projectedPointMarkers,
]

  const selectedCell = cells.find((c) => c.id === selectedId)
  const selectedMeta = selectedCell ? getRiskMeta(selectedCell.severity) : null

  return (
    <div>
      <div className={`relative ${height} w-full overflow-hidden rounded-xl border border-slate-800/60`}>
        {status === 'loading' && (
          <div className="absolute inset-0 z-[400] flex items-center justify-center bg-slate-950/70">
            <LoadingState label="Loading storm tracking…" />
          </div>
        )}
        {status === 'error' && (
          <div className="absolute inset-0 z-[400] flex items-center justify-center bg-slate-950/70 px-4">
            <ErrorState
              title="Unable to load storm data"
              message={error}
              onRetry={cellsState.load}
            />
          </div>
        )}
        {status === 'success' &&
          (cells.length > 0 || polylines.length > 0 ? (
            <>
              <LeafletMap
                center={[20.0, 78.0]}
                zoom={5}
                markers={allMarkers}
                circles={circles}
                polylines={polylines}
                fitBounds
                fitToken={fitToken}
                demo={cellsState.data?.demo ?? tracksState.data?.demo}
                demoLabel="DEMO TRACKS"
                onMarkerClick={(index) => {
                  const cell = cells[index]
                  if (cell) setSelectedId(cell.id)
                }}
              />
              <button
                onClick={() => setFitToken((t) => t + 1)}
                className="absolute right-3 top-3 z-[450] flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-950/85 px-2.5 py-1.5 text-[11px] font-semibold text-slate-300 shadow-lg backdrop-blur transition-colors hover:bg-slate-800 hover:text-sky-300"
                title="Reset map to tracked storms"
              >
                <Maximize2 className="h-3 w-3" aria-hidden="true" />
                Reset view
              </button>
              <div className="pointer-events-none absolute bottom-3 left-3 z-[450] rounded-lg border border-slate-700/70 bg-slate-950/85 px-3 py-2 shadow-lg backdrop-blur">
                <p className="mb-1.5 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-slate-400">
                  <Radar className="h-3 w-3" aria-hidden="true" /> Storm Legend
                </p>
                <div className="flex flex-col gap-1.5 text-[10px] text-slate-300">
                  <span className="flex items-center gap-2">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e]" />
                    Current position
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="inline-block h-0.5 w-5 bg-slate-300" />
                    Historical path
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="inline-block h-0 w-5 border-t-2 border-dashed border-slate-300" />
                    Projected path
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="inline-block h-2 w-2 rounded-sm bg-rose-500/25 ring-1 ring-rose-400/40" />
                    High-risk zone
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 bg-slate-950/50 px-6 text-center text-sm text-slate-500">
              <Radar className="h-7 w-7 text-slate-600" aria-hidden="true" />
              <p className="font-semibold text-slate-300">No active storm cells detected</p>
              <p className="max-w-xs text-xs text-slate-500">
                The convective grid has not observed any storm cells in the
                current observation window. New cells will appear here as soon
                as the detector reports them.
              </p>
            </div>
          ))}
      </div>

      {/* Header + legend bar */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800/40 bg-slate-950/40 px-4 py-2.5">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px]">
          <span className="flex items-center gap-1.5 font-semibold text-slate-300">
            <Radar className="h-3 w-3 text-rose-400" aria-hidden="true" />
            Storm Tracking
          </span>
          <span className="text-slate-500">Current position · historical track · projected path</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px]">
          <span className="flex items-center gap-1.5 text-slate-500">
            Intensity legend
          </span>
          {(['LOW', 'MODERATE', 'HIGH', 'EXTREME'] as RiskLevel[]).map((level) => (
            <span key={level} className="flex items-center gap-1.5">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{
                  backgroundColor: SEVERITY_COLORS[level],
                  boxShadow: `0 0 6px ${SEVERITY_COLORS[level]}44`,
                }}
              />
              <span className="font-medium text-slate-300">{level}</span>
            </span>
          ))}
          {cellsState.data?.demo && (
            <DemoModeIndicator demo note={cellsState.data.demo_note} />
          )}
        </div>
      </div>

      {/* Selected storm information panel */}
      {selectedCell && selectedMeta ? (
        <div
          id="storm-info-panel"
          className={`mt-3 rounded-xl border bg-slate-950/50 p-4 ${selectedMeta.borderClass}`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-100">
              <Navigation className="h-4 w-4" style={{ color: SEVERITY_COLORS[selectedCell.severity] }} aria-hidden="true" />
              Storm {selectedCell.id.replace(/^CB-?/i, '')}
              <span
                className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${selectedMeta.borderClass} ${selectedMeta.bgClass} ${selectedMeta.textClass}`}
              >
                {selectedMeta.label}
              </span>
            </h4>
            <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <Clock className="h-3 w-3" aria-hidden="true" />
              Updated {timeAgo(selectedCell.timestamp)}
            </span>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <StormMetric label="Location" value={`${selectedCell.latitude.toFixed(2)}°, ${selectedCell.longitude.toFixed(2)}°`} />
            <StormMetric label="Intensity" value={`${Math.round(selectedCell.intensity * 100)}%`} />
            <StormMetric label="Direction" value={`${compassDirection(selectedCell.movement_direction_deg)} · ${selectedCell.movement_direction_deg.toFixed(0)}°`} />
            <StormMetric label="Speed" value={`${selectedCell.movement_speed_kmh.toFixed(0)} km/h`} />
            <StormMetric label="Affected area" value={`≈ ${(Math.PI * selectedCell.radius_km * selectedCell.radius_km).toFixed(0)} km²`} />
            <StormMetric label="Precip" value={`${selectedCell.precipitation_mm_h.toFixed(1)} mm/h`} />
            <StormMetric
              label="Echo top"
              value={selectedCell.echo_top_km != null ? `${selectedCell.echo_top_km.toFixed(0)} km` : '—'}
            />
            {selectedCell.vil_kgm2 != null && (
              <StormMetric label="VIL" value={`${selectedCell.vil_kgm2.toFixed(0)} kg/m²`} />
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-600">
            <Ship className="h-3 w-3" aria-hidden="true" />
            <span>
              Moving {compassDirection(selectedCell.movement_direction_deg)} at{' '}
              {selectedCell.movement_speed_kmh.toFixed(0)} km/h — projected track
              shown as the dashed path on the map. Click any storm marker to
              inspect another cell. Using {cellsState.data?.demo ? 'DEMO tracking data' : 'observed cell data'}.
            </span>
          </div>
        </div>
      ) : (
        cells.length > 0 && (
          <p className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-500">
            <Crosshair className="h-3 w-3 text-rose-400" aria-hidden="true" />
            Click a storm cell on the map to inspect its track and intensity.
          </p>
        )
      )}
    </div>
  )
}

function StormMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2">
      <p className="text-[9px] font-semibold uppercase tracking-widest text-slate-500">{label}</p>
      <p className="mt-0.5 font-mono text-xs text-slate-200">{value}</p>
    </div>
  )
}