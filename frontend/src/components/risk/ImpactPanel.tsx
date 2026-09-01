import { AlertTriangle } from 'lucide-react'

interface ImpactPanelProps {
  impacts: Record<string, number>
  categories: readonly string[]
}

const CATEGORY_LABELS: Record<string, string> = {
  flooding: 'Flooding',
  roads: 'Road Disruption',
  agriculture: 'Crop / Agriculture',
  waterlogging: 'Urban Waterlogging',
  lightning: 'Lightning Danger',
  hail: 'Hail Damage',
  visibility: 'Visibility / Transport',
}

const CATEGORY_COLORS: Record<string, string> = {
  flooding: 'bg-blue-400',
  roads: 'bg-amber-400',
  agriculture: 'bg-emerald-400',
  waterlogging: 'bg-cyan-400',
  lightning: 'bg-yellow-400',
  hail: 'bg-rose-400',
  visibility: 'bg-violet-400',
}

export default function ImpactPanel({ impacts, categories }: ImpactPanelProps) {
  const maxScore = Math.max(...categories.map((c) => impacts[c] ?? 0), 0.01)

  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
        <AlertTriangle className="h-4 w-4 text-amber-400" aria-hidden="true" />
        Estimated severity per impact category, 0 (none) to 1 (severe).
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {categories.map((cat) => {
          const score = impacts[cat] ?? 0
          const color = CATEGORY_COLORS[cat] ?? 'bg-slate-400'
          const barWidth = maxScore > 0 ? (score / maxScore) * 100 : 0
          return (
            <div
              key={cat}
              className="rounded-xl border border-slate-800 bg-slate-950/40 p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-200">
                  {CATEGORY_LABELS[cat] ?? cat}
                </span>
                <span className="font-mono text-sm font-semibold text-slate-300">
                  {score.toFixed(2)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`h-full rounded-full ${color} transition-all`}
                  style={{ width: `${barWidth}%`, opacity: 0.85 }}
                />
              </div>
            </div>
          )
        })}
      </div>
      <p className="mt-3 text-xs text-slate-600 italic">
        Prototype impact model for demonstration. Not calibrated against real
        impact / damage datasets.
      </p>
    </div>
  )
}
