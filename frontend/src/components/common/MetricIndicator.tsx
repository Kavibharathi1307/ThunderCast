import type { ReactNode } from 'react'

interface MetricIndicatorProps {
  label: string
  value: ReactNode
  sublabel?: string
  accentClass?: string
  icon?: ReactNode
}

export default function MetricIndicator({
  label,
  value,
  sublabel,
  accentClass = 'text-slate-100',
  icon,
}: MetricIndicatorProps) {
  return (
    <div className="flex flex-col rounded-xl border border-slate-800/60 bg-slate-950/50 px-4 py-3">
      <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
        {icon}
        {label}
      </span>
      <span className={`mt-1 text-xl font-bold tracking-tight ${accentClass}`}>
        {value}
      </span>
      {sublabel && (
        <span className="mt-0.5 text-[11px] text-slate-500">{sublabel}</span>
      )}
    </div>
  )
}
