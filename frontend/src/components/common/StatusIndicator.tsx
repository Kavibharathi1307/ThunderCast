interface StatusIndicatorProps {
  status: 'ok' | 'down' | 'checking' | 'unknown'
  label: string
}

const CONFIG = {
  ok: {
    dot: 'bg-emerald-400',
    text: 'text-emerald-300',
    border: 'border-emerald-700/60',
    bg: 'bg-emerald-950/40',
    pulse: false,
  },
  down: {
    dot: 'bg-rose-400',
    text: 'text-rose-300',
    border: 'border-rose-700/60',
    bg: 'bg-rose-950/40',
    pulse: false,
  },
  checking: {
    dot: 'bg-amber-400',
    text: 'text-amber-300',
    border: 'border-amber-700/60',
    bg: 'bg-amber-950/40',
    pulse: true,
  },
  unknown: {
    dot: 'bg-slate-400',
    text: 'text-slate-300',
    border: 'border-slate-700/60',
    bg: 'bg-slate-800/50',
    pulse: false,
  },
} as const

export default function StatusIndicator({
  status,
  label,
}: StatusIndicatorProps) {
  const c = CONFIG[status]
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider ${c.border} ${c.bg} ${c.text}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${c.dot} ${c.pulse ? 'animate-pulse' : ''}`}
      />
      {label}
    </span>
  )
}
