interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
}

export default function ErrorState({
  title = 'Unable to load data',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-xl border border-slate-700/50 bg-slate-900/30 px-6 py-10 text-center"
      role="alert"
    >
      <div className="grid h-10 w-10 place-items-center rounded-full bg-slate-800/80">
        <svg
          className="h-5 w-5 text-slate-400"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-slate-300">{title}</h3>
      <p className="max-w-sm text-xs text-slate-500">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-300 transition-colors hover:border-sky-700 hover:bg-sky-950/40 hover:text-sky-300"
        >
          Retry
        </button>
      )}
    </div>
  )
}
