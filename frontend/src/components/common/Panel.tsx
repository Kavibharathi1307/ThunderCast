import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
}

export default function Panel({
  title,
  subtitle,
  actions,
  children,
  className = '',
}: PanelProps) {
  return (
    <section
      className={`rounded-2xl border border-slate-800 bg-slate-900/40 shadow-sm ${className}`}
    >
      {(title || actions) && (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-5 py-4">
          <div>
            {title && (
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  )
}
