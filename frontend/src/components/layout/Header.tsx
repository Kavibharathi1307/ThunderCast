import { NavLink } from 'react-router-dom'
import { CloudLightning, RefreshCw } from 'lucide-react'
import StatusIndicator from '../common/StatusIndicator'
import DemoModeIndicator from '../common/DemoModeIndicator'
import type { HealthState } from '../../hooks/useHealth'
import { useEffect, useState } from 'react'

interface HeaderProps {
  health: HealthState
  demoMode: boolean
  onMenuToggle: () => void
}

export default function Header({
  health,
  demoMode,
  onMenuToggle,
}: HeaderProps) {
  const statusLabel =
    health === 'ok'
      ? 'Operational'
      : health === 'down'
        ? 'Offline'
        : 'Checking…'
  const statusKey = health === 'ok' ? 'ok' : health === 'down' ? 'down' : 'checking'

  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-4 py-3 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuToggle}
            className="rounded-lg border border-slate-700 p-2 lg:hidden"
            aria-label="Toggle navigation menu"
          >
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round" />
            </svg>
          </button>
          <NavLink to="/" className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-sky-500/20 text-sky-300">
              <CloudLightning className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="leading-tight">
              <span className="block text-lg font-bold tracking-tight">
                ThunderCast AI
              </span>
              <span className="block text-xs text-slate-400">
                Convective Weather Intelligence &amp; Decision Support
              </span>
            </span>
          </NavLink>
        </div>

        <div className="flex items-center gap-3">
          <span
            className="hidden items-center gap-1.5 text-[11px] text-slate-500 md:flex"
            title="Last updated"
          >
            <RefreshCw className="h-3 w-3" aria-hidden="true" />
            {now.toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>

          {demoMode && <DemoModeIndicator />}
          <div className="hidden sm:block">
            <StatusIndicator status={statusKey} label={statusLabel} />
          </div>
        </div>
      </div>
    </header>
  )
}
