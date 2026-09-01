/**
 * Backend API base URL.
 *
 * Resolution order:
 *   1. VITE_API_BASE_URL  (recommended override)
 *   2. VITE_API_URL
 *   3. The deployed ThunderCast backend (works out of the box for the demo).
 *
 * To run against a local backend instead, set VITE_API_BASE_URL=http://localhost:8000
 * in frontend/.env.local before starting the dev server.
 */
export const API_URL: string =
  import.meta.env.VITE_API_BASE_URL ??
  import.meta.env.VITE_API_URL ??
  'https://thundercast-ai-backend.onrender.com'
