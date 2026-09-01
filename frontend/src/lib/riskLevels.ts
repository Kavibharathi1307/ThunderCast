import type { RiskLevel } from '../types/api'

export interface RiskLevelMeta {
  level: RiskLevel
  label: string
  textClass: string
  bgClass: string
  borderClass: string
  dotClass: string
}

const META: Record<RiskLevel, RiskLevelMeta> = {
  LOW: {
    level: 'LOW',
    label: 'Low',
    textClass: 'text-emerald-300',
    bgClass: 'bg-emerald-900/40',
    borderClass: 'border-emerald-700',
    dotClass: 'bg-emerald-400',
  },
  MODERATE: {
    level: 'MODERATE',
    label: 'Moderate',
    textClass: 'text-amber-300',
    bgClass: 'bg-amber-900/40',
    borderClass: 'border-amber-700',
    dotClass: 'bg-amber-400',
  },
  HIGH: {
    level: 'HIGH',
    label: 'High',
    textClass: 'text-orange-300',
    bgClass: 'bg-orange-900/40',
    borderClass: 'border-orange-700',
    dotClass: 'bg-orange-400',
  },
  EXTREME: {
    level: 'EXTREME',
    label: 'Extreme',
    textClass: 'text-rose-300',
    bgClass: 'bg-rose-900/40',
    borderClass: 'border-rose-700',
    dotClass: 'bg-rose-400',
  },
}

const ORDER: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'EXTREME']

export function getRiskMeta(level: RiskLevel): RiskLevelMeta {
  return META[level] ?? META.LOW
}

export function riskOrder(level: RiskLevel): number {
  return ORDER.indexOf(level)
}
