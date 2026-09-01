interface EnvironmentModeIndicatorProps {
  mode?: 'DEMO' | 'REAL'
  modelStatus?: 'UNTRAINED' | 'TRAINED' | 'FAILED' | 'STALE'
  provenance?: string
}

/**
 * Surfaces whether the app is running on DEMO (deterministic placeholder)
 * vs REAL (live data) observations, plus the model training status. This gives
 * users an explicit, honest signal about the data/model provenance.
 */
export default function EnvironmentModeIndicator({
  mode = 'DEMO',
  modelStatus = 'UNTRAINED',
  provenance,
}: EnvironmentModeIndicatorProps) {
  const isReal = mode === 'REAL'
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
          isReal
            ? 'border-emerald-700 bg-emerald-950/50 text-emerald-300'
            : 'border-amber-700 bg-amber-950/50 text-amber-300'
        }`}
        role="status"
        title={provenance}
        aria-label={`${mode} data mode`}
      >
        <span
          className={`inline-flex h-2 w-2 rounded-full ${
            isReal ? 'bg-emerald-400' : 'bg-amber-400'
          }`}
        />
        {mode === 'REAL' ? 'REAL DATA' : 'DEMO MODE'}
      </span>
      <span
        className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${
          modelStatus === 'TRAINED'
            ? 'border-emerald-700 bg-emerald-950/50 text-emerald-300'
            : 'border-slate-700 bg-slate-900/40 text-slate-400'
        }`}
        role="status"
        aria-label={`Model ${modelStatus.toLowerCase()}`}
      >
        {modelStatus === 'TRAINED' ? 'TRAINED MODEL' : 'BASELINE MODEL'}
      </span>
    </span>
  )
}
