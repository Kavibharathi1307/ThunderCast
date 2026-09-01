import { isAxiosError } from 'axios'

/**
 * Map a raw thrown error to a human-readable message that a non-technical
 * user can understand. Raw axios messages such as
 * "Request failed with status code 401" must never reach the UI.
 */
export function friendlyErrorMessage(err: unknown, fallback?: string): string {
  if (isAxiosError(err)) {
    const status = err.response?.status
    const backendMsg = (err.response?.data as Record<string, unknown>)?.detail as string | undefined

    if (status === 401 || status === 403) {
      return 'The data service requested restricted credentials. ThunderCast demo intelligence is being used instead.'
    }
    if (status === 404) {
      return 'The data service endpoint could not be found. If you are using a local backend, check that it is running the latest version.'
    }
    if (status === 422) {
      return 'The request parameters were not accepted by the weather service.'
    }
    if (status === 429) {
      return 'The weather service is busy. Please wait a moment and try again.'
    }
    if (status && status >= 500) {
      return 'The weather service is temporarily unavailable. Please try again shortly.'
    }
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      return 'The request timed out. The weather service may be slow or unavailable.'
    }
    if (!err.response) {
      return 'Cannot reach the weather service. Check your connection and try again.'
    }
    if (backendMsg) {
      return backendMsg
    }
  }

  if (err instanceof Error) {
    const msg = err.message || ''
    const lower = msg.toLowerCase()

    if (
      lower.includes('cors') ||
      lower.includes('network error') ||
      lower.includes('failed to fetch') ||
      lower.includes('err_') ||
      lower.includes('load failed')
    ) {
      return 'Cannot reach the weather service. Check your connection and try again.'
    }
    if (lower.includes('timeout')) {
      return 'The request timed out. The weather service may be slow or unavailable.'
    }
    // Strip raw axios prefix noise (e.g. "Request failed with status code 404").
    const requestFailed = lower.match(/request failed with status code (\d{3})/)
    if (requestFailed) {
      return `The weather service returned an unexpected response (HTTP ${requestFailed[1]}).`
    }
    if (msg.trim()) {
      return msg
    }
  }

  return fallback ?? 'Unable to load data. Please try again.'
}