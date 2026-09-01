interface DemoModeIndicatorProps {
  demo?: boolean
  note?: string
}

export default function DemoModeIndicator({
  demo = true,
  note,
}: DemoModeIndicatorProps) {
  if (!demo) return null
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full border border-amber-700 bg-amber-950/50 px-3 py-1 text-xs font-medium text-amber-300"
      role="status"
      title={note}
      aria-label="Demo mode active"
    >
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-400" />
      </span>
      DEMO MODE
      {note && <span className="hidden sm:inline text-amber-300/80">· {note}</span>}
    </span>
  )
}
