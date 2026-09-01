import { useCallback, useEffect, useRef, useState } from 'react'
import { friendlyErrorMessage } from '../lib/errors'

export type AsyncState<T> = {
  status: 'loading' | 'success' | 'error'
  data: T | null
  error: string | null
}

export interface UseAsyncOptions {
  auto?: boolean
}

export function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: UseAsyncOptions = {},
) {
  const { auto = true } = options
  const [state, setState] = useState<AsyncState<T>>({
    status: 'loading',
    data: null,
    error: null,
  })
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, status: 'loading', error: null }))
    try {
      const data = await fetcherRef.current()
      setState({ status: 'success', data, error: null })
    } catch (err) {
      const message = friendlyErrorMessage(
        err,
        'Unable to reach the data service.',
      )
      setState({ status: 'error', data: null, error: message })
    }
  }, [])

  useEffect(() => {
    if (!auto) return
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { ...state, load }
}
