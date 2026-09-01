import type { RiskLevel } from '../../types/api'

interface RiskIndicatorProps {
  level: RiskLevel
}

const LEVEL_ORDER: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'EXTREME']

const LEVEL_COLOR: Record<RiskLevel, string> = {
  LOW: 'bg-emerald-400',
  MODERATE: 'bg-amber-400',
  HIGH: 'bg-orange-400',
  EXTREME: 'bg-rose-500',
}

export default function RiskIndicator({ level }: RiskIndicatorProps) {
  const activeIndex = LEVEL_ORDER.indexOf(level)
  return (
    <div className="flex gap-1" role="img" aria-label={`Overall risk: ${level}`}>
      {LEVEL_ORDER.map((lvl, i) => (
        <span
          key={lvl}
          className={`h-2 flex-1 rounded-full ${
            i <= activeIndex ? LEVEL_COLOR[level] : 'bg-slate-700'
          }`}
        />
      ))}
    </div>
  )
}
