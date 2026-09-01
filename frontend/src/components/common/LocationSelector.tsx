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
}

export default function LocationSelector({
  value,
  onChange,
}: LocationSelectorProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3">
      <div className="flex-1 min-w-[200px]">
        <label
          htmlFor="location-picker"
          className="block text-xs uppercase tracking-wider text-slate-500"
        >
          Location
        </label>
        <select
          id="location-picker"
          value={value.name}
          onChange={(e) => {
            const selected = INDIA_LOCATIONS.find((l) => l.name === e.target.value)
            if (selected) onChange(selected)
          }}
          className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 focus:border-sky-500 focus:outline-none"
        >
          {INDIA_LOCATIONS.map((loc) => (
            <option key={loc.name} value={loc.name}>
              {loc.name}
            </option>
          ))}
        </select>
      </div>
      <div className="ml-auto text-right text-xs text-slate-500">
        <p>
          Lat <span className="font-mono text-slate-300">{value.latitude.toFixed(2)}</span>
        </p>
        <p>
          Lon <span className="font-mono text-slate-300">{value.longitude.toFixed(2)}</span>
        </p>
      </div>
    </div>
  )
}
