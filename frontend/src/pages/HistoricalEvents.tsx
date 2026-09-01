import { History, BarChart3 } from 'lucide-react'
import { getHistoricalAnalytics, getHistoricalEvents } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import Panel from '../components/common/Panel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import MetricIndicator from '../components/common/MetricIndicator'
import RiskBadge from '../components/risk/RiskBadge'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function HistoricalEvents() {
  const state = useAsync(() => getHistoricalEvents(), [])
  const analyticsState = useAsync(() => getHistoricalAnalytics(), [])
  const events = state.data?.events ?? []
  const analytics = analyticsState.data?.data

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Historical Events</h1>
          <p className="mt-1 text-sm text-slate-400">
            Analysis of past thunderstorm, hail &amp; cloudburst events.
          </p>
        </div>
        <DemoModeIndicator demo={state.data?.demo} note={state.data?.demo_note} />
      </div>

      {/* Analytics summary */}
      <Panel
        title="Historical Analytics"
        subtitle="Aggregate patterns from recorded events"
        actions={<DemoModeIndicator demo={analyticsState.data?.demo} note={analyticsState.data?.demo_note} />}
      >
        {analyticsState.status === 'loading' && <LoadingState label="Computing analytics…" />}
        {analyticsState.status === 'error' && (
          <ErrorState message={analyticsState.error ?? 'Analytics unavailable'} onRetry={analyticsState.load} />
        )}
        {analyticsState.status === 'success' && analytics && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <MetricIndicator
                label="Total Events"
                value={analytics.total_events}
                sublabel="Analyzed"
              />
              <MetricIndicator
                label="Peak Month"
                value={analytics.peak_activity_month}
                sublabel="Highest activity"
              />
              <MetricIndicator
                label="Most Affected"
                value={analytics.most_affected_region}
                sublabel="Region"
              />
              <MetricIndicator
                label="Avg Confidence"
                value={`${Math.round(analytics.avg_confidence * 100)}%`}
                sublabel="Historical record"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {/* Event type breakdown */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                  <BarChart3 className="h-4 w-4 text-sky-400" aria-hidden="true" />
                  Events by Type
                </h4>
                <div className="space-y-2">
                  <TypeBar
                    label="Thunderstorm"
                    count={analytics.event_types.thunderstorm}
                    total={analytics.total_events}
                    color="bg-sky-400"
                  />
                  <TypeBar
                    label="Hail"
                    count={analytics.event_types.hail}
                    total={analytics.total_events}
                    color="bg-amber-400"
                  />
                  <TypeBar
                    label="Cloudburst"
                    count={analytics.event_types.cloudburst}
                    total={analytics.total_events}
                    color="bg-violet-400"
                  />
                </div>
              </div>

              {/* Risk distribution */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                  Events by Risk Level
                </h4>
                <div className="space-y-2">
                  <RiskBar level="LOW" count={analytics.risk_distribution.low} total={analytics.total_events} />
                  <RiskBar level="MODERATE" count={analytics.risk_distribution.moderate} total={analytics.total_events} />
                  <RiskBar level="HIGH" count={analytics.risk_distribution.high} total={analytics.total_events} />
                  <RiskBar level="EXTREME" count={analytics.risk_distribution.extreme} total={analytics.total_events} />
                </div>
              </div>
            </div>

            {/* Monthly trend chart */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                Monthly Activity Trend
              </h4>
              <div className="flex items-end gap-1 h-40">
                {analytics.monthly_trends.map((trend) => {
                  const max = Math.max(...analytics.monthly_trends.map((t) => t.count))
                  const height = max > 0 ? (trend.count / max) * 100 : 0
                  const isPeak = trend.month === analytics.peak_activity_month
                  return (
                    <div
                      key={trend.month}
                      className="flex flex-1 flex-col items-center gap-1"
                    >
                      <span className="text-[10px] text-slate-500">{trend.count}</span>
                      <div
                        className={`w-full rounded-t ${
                          isPeak ? 'bg-sky-400' : 'bg-sky-900/70'
                        } hover:bg-sky-500 transition-colors`}
                        style={{ height: `${height}%` }}
                        title={`${trend.month}: ${trend.count} events`}
                      />
                      <span className="text-[9px] text-slate-600 whitespace-nowrap">
                        {trend.month.slice(5)}
                      </span>
                    </div>
                  )
                })}
              </div>
              <p className="mt-2 text-xs text-slate-600">
                Analysis period: {analytics.date_range_start} to {analytics.date_range_end}
              </p>
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Recorded Events" subtitle={`${state.data?.count ?? '—'} event(s)`}>
        {state.status === 'loading' && <LoadingState label="Loading historical events…" />}
        {state.status === 'error' && (
          <ErrorState message={state.error ?? 'Historical data unavailable'} onRetry={state.load} />
        )}
        {state.status === 'success' && events.length === 0 && (
          <EmptyState
            icon={<History className="h-8 w-8 text-slate-600" aria-hidden="true" />}
            title="No historical events"
            description="No convective events have been recorded yet."
          />
        )}
        {state.status === 'success' && events.length > 0 && (
          <ul className="space-y-3">
            {events.map((event) => (
              <li
                key={event.id ?? `${event.occurred_at}-${event.latitude}`}
                className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold capitalize text-slate-100">
                      {event.event_type.replace(/_/g, ' ')}
                    </h4>
                    {event.risk_level && <RiskBadge level={event.risk_level} />}
                  </div>
                  <span className="text-xs text-slate-500">
                    {formatDate(event.occurred_at)}
                  </span>
                </div>
                {event.location_name && (
                  <p className="mt-1 text-xs text-sky-400/80">{event.location_name}</p>
                )}
                <dl className="mt-3 grid gap-x-6 gap-y-1 text-xs text-slate-500 sm:grid-cols-3">
                  <div className="flex justify-between gap-2">
                    <dt className="shrink-0">Location</dt>
                    <dd className="text-right font-mono text-slate-400">
                      {event.latitude.toFixed(2)}, {event.longitude.toFixed(2)}
                    </dd>
                  </div>
                  {event.max_thunderstorm_probability != null && (
                    <div className="flex justify-between gap-2">
                      <dt className="shrink-0">Peak thunder</dt>
                      <dd className="text-right font-mono text-slate-400">
                        {Math.round(event.max_thunderstorm_probability * 100)}%
                      </dd>
                    </div>
                  )}
                  {event.duration_hours != null && (
                    <div className="flex justify-between gap-2">
                      <dt className="shrink-0">Duration</dt>
                      <dd className="text-right font-mono text-slate-400">
                        {event.duration_hours.toFixed(1)} hr
                      </dd>
                    </div>
                  )}
                  {event.damage_reported && (
                    <div className="col-span-full">
                      <span className="rounded-full border border-rose-800 bg-rose-950/40 px-2 py-0.5 text-xs text-rose-300">
                        Damage reported
                      </span>
                    </div>
                  )}
                </dl>
                {event.impact_summary && (
                  <p className="mt-2 text-sm text-slate-400">{event.impact_summary}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}

function TypeBar({
  label,
  count,
  total,
  color,
}: {
  label: string
  count: number
  total: number
  color: string
}) {
  const pct = total > 0 ? (count / total) * 100 : 0
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono text-slate-300">
          {count} ({Math.round(pct)}%)
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function RiskBar({
  level,
  count,
  total,
}: {
  level: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME'
  count: number
  total: number
}) {
  const pct = total > 0 ? (count / total) * 100 : 0
  return (
    <div className="flex items-center gap-2">
      <RiskBadge level={level} />
      <div className="flex-1 h-2 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full bg-gradient-to-r from-slate-600 to-slate-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs text-slate-400">{count}</span>
    </div>
  )
}
