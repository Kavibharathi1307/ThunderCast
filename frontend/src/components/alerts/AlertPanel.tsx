import { AlertTriangle, ShieldCheck } from 'lucide-react'
import type { Alert } from '../../types/api'
import { getRiskMeta } from '../../lib/riskLevels'

interface AlertPanelProps {
  alerts: Alert[]
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function timeRemaining(validUntil: string): string {
  const now = Date.now()
  const end = new Date(validUntil).getTime()
  const diff = end - now
  if (diff <= 0) return 'Expired'
  const hours = Math.floor(diff / 3600000)
  const mins = Math.floor((diff % 3600000) / 60000)
  if (hours > 0) return `${hours}h ${mins}m remaining`
  return `${mins}m remaining`
}

export default function AlertPanel({ alerts }: AlertPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-8">
        <ShieldCheck className="h-10 w-10 text-emerald-500/50" aria-hidden="true" />
        <p className="text-sm text-slate-400">No active alerts. All clear.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const meta = getRiskMeta(alert.severity)
        return (
          <div
            key={alert.id ?? `${alert.title}-${alert.issued_at}`}
            className={`rounded-xl border ${meta.borderClass} bg-slate-900/40 p-4`}
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="flex items-start gap-3">
                <AlertTriangle className={`mt-0.5 h-4 w-4 shrink-0 ${meta.textClass}`} aria-hidden="true" />
                <div>
                  <h4 className="font-semibold text-slate-100">{alert.title}</h4>
                  {alert.area_name && (
                    <p className="text-xs text-slate-500 mt-0.5">{alert.area_name}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.borderClass} ${meta.bgClass} ${meta.textClass}`}
                >
                  {meta.label}
                </span>
              </div>
            </div>

            <p className="mt-2 text-sm text-slate-400">{alert.message}</p>

            <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
              <span>Issued: {formatDate(alert.issued_at)}</span>
              <span>Valid until: {formatDate(alert.valid_until)}</span>
              <span>{timeRemaining(alert.valid_until)}</span>
              {alert.area_radius_km && (
                <span>Radius: {alert.area_radius_km} km</span>
              )}
              {alert.confidence != null && (
                <span>Confidence: {Math.round(alert.confidence * 100)}%</span>
              )}
            </div>

            {alert.impacts && alert.impacts.length > 0 && (
              <div className="mt-3 space-y-2">
                <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Expected Impacts
                </h5>
                {alert.impacts.map((impact) => (
                  <div
                    key={impact.category}
                    className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold capitalize text-slate-300">
                        {impact.category.replace(/_/g, ' ')}
                      </span>
                      {impact.affected_population && (
                        <span className="text-xs text-slate-500">
                          Pop: {impact.affected_population}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-slate-400">
                      {impact.severity_description}
                    </p>
                    <p className="mt-1 text-xs text-sky-400/80">
                      Action: {impact.recommended_action}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
