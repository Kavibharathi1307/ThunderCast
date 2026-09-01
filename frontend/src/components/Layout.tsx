import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { API_URL } from '../lib/config'
import { useHealth } from '../hooks/useHealth'
import Header from './layout/Header'
import Sidebar, { NAV_ITEMS } from './layout/Sidebar'

export default function Layout() {
  const health = useHealth()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen flex-col">
      <Header
        health={health}
        demoMode
        onMenuToggle={() => setMobileOpen((v) => !v)}
      />

      <div className="flex flex-1">
        <Sidebar />

        {mobileOpen && (
          <>
            <div
              className="fixed inset-0 z-20 bg-slate-950/60 lg:hidden"
              aria-hidden="true"
              onClick={() => setMobileOpen(false)}
            />
            <nav
              className="fixed inset-y-0 left-0 z-30 w-64 overflow-y-auto border-r border-slate-800 bg-slate-950 p-3 pt-16 lg:hidden"
              aria-label="Mobile navigation"
            >
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${
                      isActive
                        ? 'bg-sky-500/20 text-sky-300'
                        : 'text-slate-400 hover:bg-slate-800'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </NavLink>
              )
            })}
            </nav>
          </>
        )}

        <main className="min-w-0 flex-1 px-4 py-6 lg:px-6">
          <Outlet />
        </main>
      </div>

      <footer className="border-t border-slate-800 px-4 py-4 text-center text-xs text-slate-500">
        <p>
          ThunderCast AI · SIH26084 · Convective Nowcasting · 0–6 hr
        </p>
        <p className="mt-1">API: {API_URL}</p>
      </footer>
    </div>
  )
}
