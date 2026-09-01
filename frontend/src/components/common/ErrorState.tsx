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
      className="flex flex-col items-center justify-center gap-3 rounded-xl border border-rose-800 bg-rose-950/30 px-6 py-10 text-center"
      role="alert"
    >
      <span aria-hidden="true" className="text-3xl">
        ⚠️
      </span>
      <h3 className="text-sm font-semibold text-rose-300">{title}</h3>
      <p className="max-w-md text-sm text-rose-200/80">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg border border-rose-700 bg-rose-900/50 px-4 py-2 text-sm font-medium text-rose-200 transition-colors hover:bg-rose-800/60"
        >
          Retry
        </button>
      )}
    </div>
  )
}
