import { useEffect, useState } from 'react'
import { API_URL } from '../lib/config'

export type HealthState = 'checking' | 'ok' | 'down'

export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>('checking')

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)

    async function check() {
      try {
        const res = await fetch(`${API_URL}/api/health`, {
          signal: controller.signal,
        })
        if (!cancelled) setState(res.ok ? 'ok' : 'down')
      } catch {
        if (!cancelled) setState('down')
      } finally {
        clearTimeout(timeout)
      }
    }

    check()
    return () => {
      cancelled = true
      controller.abort()
      clearTimeout(timeout)
    }
  }, [])

  return state
}
