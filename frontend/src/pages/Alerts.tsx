import { Bell } from 'lucide-react'
import { getAlerts } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import Panel from '../components/common/Panel'
import AlertPanel from '../components/alerts/AlertPanel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import DemoModeIndicator from '../components/common/DemoModeIndicator'
import MetricIndicator from '../components/common/MetricIndicator'
import { getRiskMeta } from '../lib/riskLevels'

export default function Alerts() {
  const state = useAsync(() => getAlerts(), [])
  const alerts = state.data?.alerts ?? []

  const extremeCount = alerts.filter((a) => a.severity === 'EXTREME').length
  const highCount = alerts.filter((a) => a.severity === 'HIGH').length
  const moderateCount = alerts.filter((a) => a.severity === 'MODERATE').length
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Alerts</h1>
          <p className="mt-1 text-sm text-slate-400">
            Impact-based warnings for communities and authorities.
          </p>
        </div>
        <DemoModeIndicator demo={state.data?.demo} note={state.data?.demo_note} />
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricIndicator label="Active Alerts" value={alerts.length} sublabel="Total warnings" />
        <MetricIndicator label="Extreme" value={extremeCount} sublabel="Severe threat" />
        <MetricIndicator label="High" value={highCount} sublabel="Significant risk" />
        <MetricIndicator label="Moderate" value={moderateCount} sublabel="Elevated risk" />
      </div>

      <Panel title="Active Alerts" subtitle={`${state.data?.count ?? '—'} alert(s)`}>
        {state.status === 'loading' && <LoadingState label="Loading alerts…" />}
        {state.status === 'error' && (
          <ErrorState message={state.error ?? 'Alert data unavailable'} onRetry={state.load} />
        )}
        {state.status === 'success' && (
          <AlertPanel alerts={alerts} />
        )}
      </Panel>

      {alerts.length > 0 && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
            <Bell className="h-4 w-4 text-amber-400" aria-hidden="true" />
            Alert Severity Legend
          </h2>
          <div className="space-y-2">
            {(['EXTREME', 'HIGH', 'MODERATE', 'LOW'] as const).map((lvl) => {
              const meta = getRiskMeta(lvl)
              return (
                <div key={lvl} className="flex items-center gap-3">
                  <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.borderClass} ${meta.bgClass} ${meta.textClass}`}>
                    {meta.label}
                  </span>
                  <p className="text-xs text-slate-500">{metaDescription(lvl)}</p>
                </div>
              )
            })}
          </div>
        </section>
      )}
    </div>
  )
}

function metaDescription(level: 'EXTREME' | 'HIGH' | 'MODERATE' | 'LOW'): string {
  switch (level) {
    case 'EXTREME':
      return 'Take protective action immediately. Severe convective threat.'
    case 'HIGH':
      return 'Significant hazard potential. Precautions recommended.'
    case 'MODERATE':
      return 'Elevated convective potential. Some localized impact possible.'
    case 'LOW':
      return 'Minimal convective hazard expected. Routine monitoring.'
  }
}
