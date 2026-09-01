interface StatusIndicatorProps {
  status: 'ok' | 'down' | 'checking' | 'unknown'
  label: string
}

const CONFIG = {
  ok: {
    dot: 'bg-emerald-400',
    text: 'text-emerald-300',
    border: 'border-emerald-700',
    bg: 'bg-emerald-900/40',
    pulse: false,
  },
  down: {
    dot: 'bg-rose-400',
    text: 'text-rose-300',
    border: 'border-rose-700',
    bg: 'bg-rose-900/40',
    pulse: false,
  },
  checking: {
    dot: 'bg-amber-400',
    text: 'text-amber-300',
    border: 'border-amber-700',
    bg: 'bg-amber-900/40',
    pulse: true,
  },
  unknown: {
    dot: 'bg-slate-400',
    text: 'text-slate-300',
    border: 'border-slate-700',
    bg: 'bg-slate-800',
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
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium ${c.border} ${c.bg} ${c.text}`}
    >
      <span
        className={`h-2 w-2 rounded-full ${c.dot} ${c.pulse ? 'animate-pulse' : ''}`}
      />
      {label}
    </span>
  )
}
