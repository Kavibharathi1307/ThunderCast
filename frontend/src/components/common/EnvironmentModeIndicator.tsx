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
      <span
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
          isReal
            ? 'border-emerald-700 bg-emerald-950/50 text-emerald-300'
            : 'border-amber-600/50 bg-amber-950/40 text-amber-300'
        }`}
        role="status"
        title={provenance}
        aria-label={`${mode} data mode`}
      >
        <span
          className={`inline-flex h-1.5 w-1.5 rounded-full ${
            isReal ? 'bg-emerald-400' : 'bg-amber-400'
          }`}
        />
        {isReal ? 'LIVE DATA' : 'DEMO DATA'}
      </span>
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
