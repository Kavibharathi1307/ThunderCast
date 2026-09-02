import { useState } from 'react'
import { MapPin, LocateFixed } from 'lucide-react'
import type { LocationPoint } from '../../types/api'

export const DEFAULT_LOCATION: LocationPoint = {
  name: 'Mumbai',
  latitude: 19.076,
  longitude: 72.8777,
}

export const INDIA_LOCATIONS: LocationPoint[] = [
  { name: 'Mumbai', latitude: 19.076, longitude: 72.8777 },
  { name: 'Delhi NCR', latitude: 28.6139, longitude: 77.209 },
  { name: 'Chennai', latitude: 13.0827, longitude: 80.2707 },
  { name: 'Kolkata', latitude: 22.5726, longitude: 88.3639 },
  { name: 'Hyderabad', latitude: 17.385, longitude: 78.4867 },
  { name: 'Bengaluru', latitude: 12.9716, longitude: 77.5946 },
  { name: 'Jaipur', latitude: 26.9124, longitude: 75.7873 },
  { name: 'Bhopal', latitude: 23.2599, longitude: 77.4126 },
  { name: 'Ahmedabad', latitude: 23.0225, longitude: 72.5714 },
  { name: 'Lucknow', latitude: 26.8467, longitude: 80.9462 },
  { name: 'Guwahati', latitude: 26.1445, longitude: 91.7362 },
  { name: 'Patna', latitude: 25.6093, longitude: 85.1376 },
]

interface LocationSelectorProps {
  value: LocationPoint
  onChange: (location: LocationPoint) => void
  /** When false (real live data), the status pill shows LIVE WEATHER DATA. */
  demo?: boolean
}

export default function LocationSelector({
  value,
  onChange,
  demo = true,
}: LocationSelectorProps) {
  const [locating, setLocating] = useState(false)
  const [geoError, setGeoError] = useState<string | null>(null)

  function useMyLocation() {
    if (!('geolocation' in navigator)) {
      setGeoError('Geolocation is not supported by this browser.')
      return
    }
    setLocating(true)
    setGeoError(null)

    const success = (pos: GeolocationPosition) => {
      const lat = pos.coords.latitude
      const lon = pos.coords.longitude
      onChange({
        name: `Current location (${lat.toFixed(2)}, ${lon.toFixed(2)})`,
        latitude: Number(lat.toFixed(4)),
        longitude: Number(lon.toFixed(4)),
      })
      setLocating(false)
    }

    const error = (err: GeolocationPositionError) => {
      setLocating(false)
      switch (err.code) {
        case err.PERMISSION_DENIED:
          setGeoError(
            'Location permission was denied. Allow location access in your browser and try again.',
          )
          break
        case err.POSITION_UNAVAILABLE:
          setGeoError(
            'Your current position is unavailable. Check that device location is enabled, or pick a city below.',
          )
          break
        case err.TIMEOUT:
          setGeoError(
            'Timed out while determining your location. Try again, or pick a city below.',
          )
          break
        default:
          setGeoError('Unable to determine your location. Pick a city below.')
      }
    }

    navigator.geolocation.getCurrentPosition(success, error, {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 30000,
    })
  }

  return (
    <div className="flex flex-wrap items-center gap-4 rounded-xl border border-slate-800/60 bg-slate-900/50 px-5 py-3.5">
      <div className="flex items-center gap-2.5">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-sky-500/10 text-sky-400">
          <MapPin className="h-4 w-4" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <label
            htmlFor="location-picker"
            className="block text-[10px] font-semibold uppercase tracking-widest text-slate-500"
          >
            Selected Location
          </label>
          <div className="mt-0.5 flex items-center gap-2">
            <select
              id="location-picker"
              value={value.name}
              onChange={(e) => {
                const selected = INDIA_LOCATIONS.find(
                  (l) => l.name === e.target.value,
                )
                if (selected) onChange(selected)
                setGeoError(null)
              }}
              className="block cursor-pointer rounded-lg border-none bg-transparent text-sm font-semibold text-slate-100 focus:outline-none"
            >
              {!INDIA_LOCATIONS.some((l) => l.name === value.name) && (
                <option value={value.name} className="bg-slate-900 text-sky-300">
                  {value.name}
                </option>
              )}
              {INDIA_LOCATIONS.map((loc) => (
                <option
                  key={loc.name}
                  value={loc.name}
                  className="bg-slate-900 text-slate-200"
                >
                  {loc.name}
                </option>
              ))}
            </select>
            <button
              onClick={useMyLocation}
              disabled={locating}
              className="inline-flex shrink-0 items-center gap-1 rounded-md border border-slate-700 px-2 py-1 text-[11px] font-medium text-slate-300 transition-colors hover:border-sky-700 hover:bg-sky-950/40 hover:text-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
              title="Use your current location"
            >
              <LocateFixed
                className={`h-3 w-3 ${locating ? 'animate-pulse' : ''}`}
                aria-hidden="true"
              />
              {locating ? 'Locating…' : 'Use my location'}
            </button>
          </div>
        </div>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <div className="text-right">
          <p className="text-[10px] uppercase tracking-widest text-slate-600">
            Coordinates
          </p>
          <p className="font-mono text-xs text-slate-300">
            {value.latitude.toFixed(2)}°N, {value.longitude.toFixed(2)}°E
          </p>
        </div>
        <div className="hidden h-8 w-px bg-slate-800 sm:block" />
        <DataStatusPill demo={demo} />
      </div>

      {geoError && (
        <p className="w-full text-[11px] text-amber-300/90">{geoError}</p>
      )}
    </div>
  )
}

function DataStatusPill({ demo }: { demo: boolean }) {
  if (demo) return null
  return (
    <span
      className="inline-flex items-center gap-1.5"
      role="status"
      aria-label="Live weather data"
    >
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
      </span>
      <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300">
        LIVE WEATHER DATA
      </span>
    </span>
  )
}