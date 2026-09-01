import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Map,
  LineChart,
  Radar,
  Bell,
  History,
  BookOpen,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/forecast', label: 'Forecast', icon: LineChart },
  { to: '/risk-map', label: 'Risk Map', icon: Map },
  { to: '/storm-tracking', label: 'Storm Tracking', icon: Radar },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/historical-events', label: 'Historical Events', icon: History },
  { to: '/methodology', label: 'Methodology', icon: BookOpen },
]

export default function Sidebar() {
  return (
    <aside
      className="hidden w-60 shrink-0 border-r border-slate-800 bg-slate-950/60 lg:block"
      aria-label="Primary navigation"
    >
      <nav className="sticky top-0 flex flex-col gap-1 p-3">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-300'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`
              }
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
