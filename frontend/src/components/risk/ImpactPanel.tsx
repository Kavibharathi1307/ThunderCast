import { AlertTriangle, ShieldAlert, ShieldCheck } from 'lucide-react'
import { getRiskMeta } from '../../lib/riskLevels'
import type { RiskLevelMeta } from '../../lib/riskLevels'

interface ImpactPanelProps {
  impacts: Record<string, number>
  categories: readonly string[]
  label?: string
}

const CATEGORY_LABELS: Record<string, string> = {
  flooding: 'Flooding',
  roads: 'Road Disruption',
  agriculture: 'Crop / Agriculture',
  waterlogging: 'Urban Waterlogging',
  lightning: 'Lightning Danger',
  hail: 'Hail Damage',
  visibility: 'Visibility / Transport',
  wind_damage: 'Wind Damage',
  power_outage: 'Power Outage',
}

// Group raw impact keys into high-level operational categories for a clean,
// plain-language summary card layout.
const GROUP_ORDER: { group: string; keys: string[] }[] = [
  { group: 'Infrastructure', keys: ['power_outage', 'roads'] },
  { group: 'Transport', keys: ['visibility', 'roads'] },
  { group: 'Agriculture', keys: ['agriculture', 'hail'] },
  { group: 'Public Safety', keys: ['lightning', 'flooding'] },
]

function keyToLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key.replace(/_/g, ' ')
}

function scoreToSeverity(score: number): { level: RiskLevelMeta; pct: number } {
  const pct = Math.max(0, Math.min(100, Math.round(score * 100)))
  if (score >= 0.75) return { level: getRiskMeta('EXTREME'), pct }
  if (score >= 0.6) return { level: getRiskMeta('HIGH'), pct }
  if (score >= 0.4) return { level: getRiskMeta('MODERATE'), pct }
  return { level: getRiskMeta('LOW'), pct }
}

export default function ImpactPanel({
  impacts,
  categories,
  label,
}: ImpactPanelProps) {
  const scored = categories.map((c) => {
    const raw = impacts[c] ?? 0
    const { level, pct } = scoreToSeverity(raw)
    return { category: c, raw, level, pct }
  })
  const overallRaw =
    scored.length > 0 ? Math.max(...scored.map((s) => s.raw)) : 0
  const overall = scoreToSeverity(overallRaw)

  // Build grouped rows (dedupe keys within a group).
  const grouped = GROUP_ORDER.map((g) => {
    const groupRaw = Math.max(
      ...g.keys.map((k) => (k in impacts ? impacts[k] : 0)),
    )
    const { level, pct } = scoreToSeverity(groupRaw)
    const keyLabel = g.keys
      .filter((k) => k in impacts)
      .map(keyToLabel)
      .join(' · ')
    return { group: g.group, raw: groupRaw, level, pct, sub: keyLabel || g.group }
  }).filter((r) => r.raw > 0)

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <AlertTriangle className="h-4 w-4 text-amber-400" aria-hidden="true" />
          {label ?? 'Prototype impact model'} · 0 (none) – 1 (severe)
        </div>
        <div
          className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 ${overall.level.borderClass} ${overall.level.bgClass}`}
        >
          {overallRaw >= 0.6 ? (
            <ShieldAlert
              className={`h-4 w-4 ${overall.level.textClass}`}
              aria-hidden="true"
            />
          ) : (
            <ShieldCheck
              className={`h-4 w-4 ${overall.level.textClass}`}
              aria-hidden="true"
            />
          )}
          <span className={`text-sm font-bold ${overall.level.textClass}`}>
            Overall Impact: {overall.level.label.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Grouped plain-language impact rows with progress bars */}
      <div className="space-y-3">
        {grouped.length > 0 &&
          grouped.map(({ group, level, pct, sub }) => (
            <div
              key={group}
              className="rounded-xl border border-slate-800 bg-slate-950/40 p-4"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <span className="text-sm font-medium text-slate-200">
                    {group}
                  </span>
                  <span className="ml-2 text-[11px] text-slate-500">{sub}</span>
                </div>
                <span
                  className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${level.borderClass} ${level.bgClass} ${level.textClass}`}
                >
                  {level.label}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full ${level.dotClass} transition-all`}
                    style={{ width: `${pct}%`, opacity: 0.9 }}
                  />
                </div>
                <span className="w-10 shrink-0 text-right font-mono text-[11px] text-slate-400">
                  {pct}%
                </span>
              </div>
            </div>
          ))}
      </div>

      {/* Detailed per-category breakdown */}
      <div className="mt-4">
        <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          Detailed categories
        </h4>
        <div className="grid gap-2 sm:grid-cols-2">
          {scored.map(({ category, raw, level }) => (
            <div
              key={category}
              className="flex items-center justify-between rounded-lg border border-slate-800/60 bg-slate-900/30 px-3 py-2"
              title={`${keyToLabel(category)} — ${Math.round(raw * 100)}%`}
            >
              <span className="text-xs text-slate-300">{keyToLabel(category)}</span>
              <span className={`text-xs font-mono font-semibold ${level.textClass}`}>
                {Math.round(raw * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-600 italic">
        Prototype impact model for demonstration. Not calibrated against real
        impact / damage datasets.
      </p>
    </div>
  )
}