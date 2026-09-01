import { Info } from 'lucide-react'

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
      className="group/tooltip relative inline-flex items-center gap-1.5 rounded-full border border-amber-600/50 bg-amber-950/40 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-amber-300"
      role="status"
      aria-label="Demo mode active"
    >
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-60" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-amber-400" />
      </span>
      DEMO
      {note && (
        <span className="ml-1 hidden text-amber-300/60 sm:inline">{note}</span>
      )}
      <span className="pointer-events-none absolute -bottom-1 right-0 z-30 mb-6 hidden w-64 rounded-lg border border-slate-700 bg-slate-800 p-3 text-left text-xs font-normal normal-case tracking-normal text-slate-300 shadow-xl group-hover/tooltip:block">
        <Info className="mb-1 inline h-3 w-3 text-amber-400" /> ThunderCast is
        currently using demonstration data. Connect supported data sources for
        live operational data.
      </span>
    </span>
  )
}
