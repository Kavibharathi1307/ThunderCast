import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
  noPadding?: boolean
}

export default function Panel({
  title,
  subtitle,
  actions,
  children,
  className = '',
  noPadding = false,
}: PanelProps) {
  return (
    <section
      className={`overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/50 backdrop-blur-sm ${className}`}
    >
      {(title || actions) && (
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/60 px-5 py-4">
          <div className="min-w-0">
            {title && (
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-300">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={noPadding ? '' : 'p-5'}>{children}</div>
    </section>
  )
}
