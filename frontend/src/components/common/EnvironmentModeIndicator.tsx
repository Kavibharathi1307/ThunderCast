interface EnvironmentModeIndicatorProps {
  mode?: 'DEMO' | 'REAL'
  modelStatus?: 'UNTRAINED' | 'TRAINED' | 'FAILED' | 'STALE'
  provenance?: string
}

export default function EnvironmentModeIndicator({
  mode = 'DEMO',
  modelStatus = 'UNTRAINED',
  provenance,
}: EnvironmentModeIndicatorProps) {
  const isReal = mode === 'REAL'
  return (
    <span className="inline-flex items-center gap-1.5">
      {isReal && (
        <span
          className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider border-emerald-700 bg-emerald-950/50 text-emerald-300"
          role="status"
          title={provenance}
          aria-label={`${mode} data mode`}
        >
          <span className="inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
          LIVE DATA
        </span>
      )}
      <span
        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
          modelStatus === 'TRAINED'
            ? 'border-emerald-700 bg-emerald-950/50 text-emerald-300'
            : 'border-slate-700 bg-slate-800/50 text-slate-400'
        }`}
        role="status"
        aria-label={`Model ${modelStatus.toLowerCase()}`}
      >
        {modelStatus === 'TRAINED' ? 'TRAINED' : 'BASELINE'}
      </span>
    </span>
  )
}
