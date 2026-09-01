import { getRiskMeta } from '../../lib/riskLevels'
import type { RiskLevel } from '../../types/api'

interface HazardCardProps {
  title: string
  icon: React.ReactNode
  probability: number
  riskLevel: RiskLevel
  confidence: number
  explanation: string | null
}

export default function HazardCard({
  title,
  icon,
  probability,
  riskLevel,
  confidence,
  explanation,
}: HazardCardProps) {
  const meta = getRiskMeta(riskLevel)
  const pct = Math.round(probability * 100)
  const confPct = Math.round(confidence * 100)

  return (
    <article
      className={`flex flex-col rounded-2xl border bg-slate-900/40 p-5 ${meta.borderClass}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-xl ${meta.textClass}`} aria-hidden="true">
            {icon}
          </span>
          <h3 className="font-semibold text-slate-200">{title}</h3>
        </div>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.borderClass} ${meta.bgClass} ${meta.textClass}`}
        >
          {meta.label}
        </span>
      </div>

      <div className="mt-4 flex items-end justify-between">
        <div>
          <span className="text-4xl font-bold text-slate-100">{pct}%</span>
          <span className="ml-1 text-sm text-slate-500">probability</span>
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>Confidence</p>
          <p className="font-mono text-slate-300">{confPct}%</p>
        </div>
      </div>

      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${meta.dotClass} transition-all`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${title} probability ${pct}%`}
        />
      </div>

      {explanation && (
        <p className="mt-3 text-xs text-slate-400">{explanation}</p>
      )}
    </article>
  )
}
