import type { RiskLevel } from '../../types/api'
import { getRiskMeta } from '../../lib/riskLevels'

interface RiskBadgeProps {
  level: RiskLevel
  className?: string
}

export default function RiskBadge({ level, className = '' }: RiskBadgeProps) {
  const meta = getRiskMeta(level)
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.borderClass} ${meta.bgClass} ${meta.textClass} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dotClass}`} />
      {meta.label}
    </span>
  )
}
