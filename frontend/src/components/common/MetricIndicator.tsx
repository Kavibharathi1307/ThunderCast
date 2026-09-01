import type { ReactNode } from 'react'

interface MetricIndicatorProps {
  label: string
  value: ReactNode
  sublabel?: string
  accentClass?: string
}

export default function MetricIndicator({
  label,
  value,
  sublabel,
  accentClass = 'text-slate-100',
}: MetricIndicatorProps) {
  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3">
      <span className="text-xs uppercase tracking-wider text-slate-500">
        {label}
      </span>
      <span className={`mt-1 text-2xl font-bold ${accentClass}`}>{value}</span>
      {sublabel && <span className="mt-0.5 text-xs text-slate-500">{sublabel}</span>}
    </div>
  )
}
