import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
}

export default function EmptyState({
  title,
  description,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-700 bg-slate-900/30 px-6 py-12 text-center">
      {icon && <div aria-hidden="true" className="text-3xl">{icon}</div>}
      <h3 className="text-sm font-semibold text-slate-300">{title}</h3>
      {description && (
        <p className="max-w-md text-sm text-slate-500">{description}</p>
      )}
    </div>
  )
}
