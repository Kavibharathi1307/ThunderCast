import {
  Sun,
  CloudSun,
  CloudRain,
  CloudRainWind,
  CloudLightning,
  CloudHail,
  Droplets,
  Wind,
  Timer,
} from 'lucide-react'
import type { ForecastPoint, RiskLevel } from '../../types/api'
import { getRiskMeta, riskFromProbability } from '../../lib/riskLevels'

interface ForecastTimelineProps {
  points: ForecastPoint[]
  overallRisk: RiskLevel
}

type HourRow = {
  lead: number
  timeLabel: string
  timestamp: string
  iconKind: 'storm' | 'hail' | 'rain' | 'drizzle' | 'cloud' | 'clear'
  risk: RiskLevel
  thunder: number
  hail: number
  burst: number
  precip: number | null
  wind: number | null
  confidence: number | null
}

function iconFor(row: HourRow) {
  const cls = 'h-6 w-6'
  switch (row.iconKind) {
    case 'storm':
      return <CloudLightning className={`${cls} text-sky-300`} aria-hidden="true" />
    case 'hail':
      return <CloudHail className={`${cls} text-rose-300`} aria-hidden="true" />
    case 'rain':
      return <CloudRainWind className={`${cls} text-blue-400`} aria-hidden="true" />
    case 'drizzle':
      return <CloudRain className={`${cls} text-sky-400/80`} aria-hidden="true" />
    case 'cloud':
      return <CloudSun className={`${cls} text-slate-400`} aria-hidden="true" />
    default:
      return <Sun className={`${cls} text-amber-300`} aria-hidden="true" />
  }
}

function classifyIcon(row: HourRow): HourRow['iconKind'] {
  const peak = Math.max(row.thunder, row.hail, row.burst)
  if (row.thunder >= 0.6) return 'storm'
  if (row.hail >= 0.4 && row.hail >= row.thunder) return 'hail'
  if (row.thunder >= 0.4 || row.burst >= 0.4) return 'rain'
  if (peak >= 0.25) return 'drizzle'
  if (row.thunder >= 0.15 || row.burst >= 0.15) return 'cloud'
  return 'clear'
}

export default function ForecastTimeline({
  points,
  overallRisk,
}: ForecastTimelineProps) {
  const rows: HourRow[] = points.map((p) => {
    const risk = riskFromProbability(
      Math.max(p.thunderstorm_probability, p.hail_probability, p.cloudburst_probability),
    )
    const base: HourRow = {
      lead: p.lead_time_hours,
      timeLabel: p.timestamp
        ? new Date(p.timestamp).toLocaleTimeString(undefined, {
            hour: 'numeric',
          })
        : p.lead_time_hours === 0
          ? 'Now'
          : `+${p.lead_time_hours}h`,
      timestamp: p.timestamp,
      iconKind: 'clear',
      risk,
      thunder: p.thunderstorm_probability,
      hail: p.hail_probability,
      burst: p.cloudburst_probability,
      precip: p.precipitation_mm,
      wind: p.wind_speed_ms,
      confidence: null,
    }
    return { ...base, iconKind: classifyIcon(base) }
  })

  const overallMeta = getRiskMeta(overallRisk)
  const startLabel = rows[0]?.timestamp
    ? new Date(rows[0].timestamp).toLocaleTimeString(undefined, {
        hour: 'numeric',
      })
    : 'Now'
  const endLabel = rows[rows.length - 1]?.timestamp
    ? new Date(rows[rows.length - 1].timestamp).toLocaleTimeString(undefined, {
        hour: 'numeric',
      })
    : '+6h'

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <Timer className="h-3.5 w-3.5 text-sky-400" aria-hidden="true" />
          Next 6 hours · {startLabel} → {endLabel}
        </p>
        <div className="flex items-center gap-2">
          <span
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${overallMeta.borderClass} ${overallMeta.bgClass} ${overallMeta.textClass}`}
          >
            Overall: {overallMeta.label}
          </span>
        </div>
      </div>

      {/* Horizontal scrollable timeline of hourly columns */}
      <div className="overflow-x-auto pb-2">
        <div className="grid min-w-[560px] grid-cols-7 gap-2">
          {rows.map((row) => {
            const meta = getRiskMeta(row.risk)
            return (
              <div
                key={row.lead}
                title={`${row.timeLabel} — ${meta.label} convective risk`}
                className={`flex flex-col rounded-xl border bg-slate-950/50 p-3 ${meta.borderClass}`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-bold ${meta.textClass}`}>
                    {row.lead === 0 ? 'Now' : row.timeLabel}
                  </span>
                  <span
                    className={`rounded-full border px-1.5 py-0.5 text-[8px] font-bold uppercase ${meta.borderClass} ${meta.bgClass} ${meta.textClass}`}
                  >
                    {meta.label}
                  </span>
                </div>

                <div className="mt-3 flex items-center justify-center">
                  {iconFor(row)}
                </div>

                <div className="mt-3 space-y-1.5">
                  <ProbabilityRow label="Thunder" value={row.thunder} color="bg-sky-400" />
                  <ProbabilityRow label="Hail" value={row.hail} color="bg-rose-400" />
                  <ProbabilityRow label="Burst" value={row.burst} color="bg-violet-400" />
                </div>

                {(row.precip != null || row.wind != null) && (
                  <div className="mt-3 space-y-1 border-t border-slate-800/40 pt-2 text-[10px]">
                    {row.precip != null && (
                      <span className="flex items-center justify-between text-slate-400">
                        <span className="flex items-center gap-1">
                          <Droplets className="h-3 w-3 text-blue-400" aria-hidden="true" />
                          Rain
                        </span>
                        <span className="font-mono text-slate-300">
                          {row.precip.toFixed(1)} mm
                        </span>
                      </span>
                    )}
                    {row.wind != null && (
                      <span className="flex items-center justify-between text-slate-400">
                        <span className="flex items-center gap-1">
                          <Wind className="h-3 w-3 text-cyan-400" aria-hidden="true" />
                          Wind
                        </span>
                        <span className="font-mono text-slate-300">
                          {row.wind.toFixed(1)} m/s
                        </span>
                      </span>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      <p className="mt-2 text-[11px] text-slate-600">
        Probabilities per lead hour. Demo intelligence produces this timeline;
        it is not a trained forecast model.
      </p>
    </div>
  )
}

function ProbabilityRow({ label, value, color }: {
  label: string
  value: number
  color: string
}) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-1.5">
      <span className="w-10 shrink-0 text-[9px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${pct}%`, opacity: 0.9 }}
        />
      </div>
      <span className="w-7 shrink-0 text-right font-mono text-[10px] text-slate-400">
        {pct}%
      </span>
    </div>
  )
}