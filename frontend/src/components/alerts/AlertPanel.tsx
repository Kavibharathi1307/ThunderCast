import { AlertTriangle, ShieldCheck, MapPin, Clock, Info } from 'lucide-react'
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

export default function AlertPanel({ alerts }: AlertPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-12">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-emerald-950/40">
          <ShieldCheck className="h-7 w-7 text-emerald-400/80" aria-hidden="true" />
        </div>
        <p className="text-sm font-semibold text-slate-200">No active alerts</p>
        <p className="max-w-sm text-center text-sm text-slate-500">
          No significant hazards are currently reported for the selected
          location.
        </p>
        <span className="rounded-full border border-slate-700 bg-slate-800/40 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          All clear
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const meta = getRiskMeta(alert.severity)
        const hazard =
          alert.title.split('—')[0].replace(/risk/gi, '').trim() || 'Convective'
        return (
          <article
            key={alert.id ?? `${alert.title}-${alert.issued_at}`}
            className={`overflow-hidden rounded-xl border bg-slate-900/40 ${meta.borderClass}`}
          >
            <div
              className={`flex items-start justify-between gap-2 border-b px-4 py-3 ${meta.borderClass} ${meta.bgClass}`}
            >
              <div className="flex items-start gap-3">
                <AlertTriangle
                  className={`mt-0.5 h-5 w-5 shrink-0 ${meta.textClass}`}
                  aria-hidden="true"
                />
                <div>
                  <h4 className="font-semibold leading-tight text-slate-100">
                    {alert.title}
                  </h4>
                  <p className="mt-0.5 text-xs text-slate-300/80">
                    {alert.message}
                  </p>
                </div>
              </div>
              <span
                className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase ${meta.borderClass} ${meta.bgClass} ${meta.textClass}`}
              >
                {meta.label.toUpperCase()}
              </span>
            </div>

            <div className="grid gap-x-6 gap-y-2 px-4 py-3 text-xs text-slate-400 sm:grid-cols-2">
              <span className="flex items-center gap-2">
                <MapPin className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
                <span className="text-slate-500">Hazard:</span>{' '}
                <span className="capitalize text-slate-300">{hazard}</span>
              </span>
              <span className="flex items-center gap-2">
                <MapPin className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
                <span className="text-slate-500">Location:</span>{' '}
                <span className="text-slate-300">
                  {alert.area_name ?? 'Selected analysis area'}
                </span>
              </span>
              <span className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
                <span className="text-slate-500">Valid:</span>{' '}
                <span className="text-slate-300">
                  {formatDate(alert.issued_at)} – {formatDate(alert.valid_until)}
                </span>
              </span>
              {alert.area_radius_km != null && (
                <span className="flex items-center gap-2">
                  <Info className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
                  <span className="text-slate-500">Coverage:</span>{' '}
                  <span className="text-slate-300">
                    {alert.area_radius_km} km radius
                  </span>
                </span>
              )}
              {alert.confidence != null && (
                <span className="flex items-center gap-2">
                  <span className="inline-flex h-2 w-2 rounded-full bg-slate-600" />
                  <span className="text-slate-500">Confidence:</span>{' '}
                  <span className="text-slate-300">
                    {Math.round(alert.confidence * 100)}%
                  </span>
                </span>
              )}
            </div>

            {alert.impacts && alert.impacts.length > 0 && (
              <div className="space-y-2 border-t border-slate-800/60 px-4 py-3">
                <h5 className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  Impact &amp; Recommended Action
                </h5>
                {alert.impacts.map((impact) => (
                  <div
                    key={impact.category}
                    className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs font-semibold capitalize text-slate-300">
                        {impact.category.replace(/_/g, ' ')}
                      </span>
                      {impact.affected_population && (
                        <span className="text-[11px] text-slate-500">
                          Pop: {impact.affected_population}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-slate-400">
                      {impact.severity_description}
                    </p>
                    <p className="mt-1 text-xs text-sky-400/90">
                      Recommended action: {impact.recommended_action}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </article>
        )
      })}
    </div>
  )
}