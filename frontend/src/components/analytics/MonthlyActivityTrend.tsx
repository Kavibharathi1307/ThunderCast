import { BarChart3 } from 'lucide-react'
import type { MonthlyTrend } from '../../types/api'

interface Props {
  trends: MonthlyTrend[]
  peakMonth: string
  dateRangeStart: string
  dateRangeEnd: string
}

export default function MonthlyActivityTrend({
  trends,
  peakMonth,
  dateRangeStart,
  dateRangeEnd,
}: Props) {
  const max = trends.length ? Math.max(...trends.map((t) => t.count)) : 0

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
      <h4 className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <BarChart3 className="h-4 w-4 text-sky-400" aria-hidden="true" />
        Monthly Activity Trend
      </h4>

      <div className="flex h-44 items-end gap-1.5">
        {trends.map((trend) => {
          const height = max > 0 ? (trend.count / max) * 100 : 0
          const isPeak = trend.month === peakMonth
          return (
            <div
              key={trend.month}
              className="group flex flex-1 flex-col items-center gap-1"
              title={`${trend.month}: ${trend.count} events${isPeak ? ' (peak)' : ''}`}
            >
              <span className="text-[9px] text-slate-500 opacity-0 transition-opacity group-hover:opacity-100">
                {trend.count}
              </span>
              <div
                className={`w-full rounded-t transition-colors ${
                  isPeak
                    ? 'bg-gradient-to-t from-sky-600 to-sky-300'
                    : 'bg-sky-900/70 hover:bg-sky-600/60'
                }`}
                style={{ height: `${height}%`, minHeight: isPeak ? 16 : 6 }}
              />
              <span
                className={`whitespace-nowrap text-[10px] font-medium ${
                  isPeak ? 'text-sky-300' : 'text-slate-600'
                }`}
              >
                {trend.month.slice(2)}
              </span>
            </div>
          )
        })}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/60 pt-3 text-[11px] text-slate-500">
        <span>
          Analysis period: {dateRangeStart} → {dateRangeEnd}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-gradient-to-t from-sky-600 to-sky-300" />
          Peak month: <span className="font-semibold text-sky-300">{peakMonth}</span>
        </span>
      </div>
    </div>
  )
}