import { useCallback, useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export interface MapMarker {
  latitude: number
  longitude: number
  label: string
  color: string
  radius?: number
  /** Optional pre-built DivIcon; overrides the default circle icon. */
  icon?: L.DivIcon
}

export interface MapCircle {
  latitude: number
  longitude: number
  radiusKm: number
  color: string
  fillOpacity?: number
}

export interface MapPolyline {
  positions: { latitude: number; longitude: number }[]
  color: string
  weight?: number
  dashArray?: string
  label?: string
  arrows?: boolean
}

/** A rectangular geographic cell (used for the convective risk grid). */
export interface MapRect {
  latitude: number
  longitude: number
  /** Full lat + lng extents in degrees (centered on latitude/longitude). */
  spanLat: number
  spanLng: number
  color: string
  fillOpacity?: number
  label?: string
}

interface LeafletMapProps {
  center?: [number, number]
  zoom?: number
  markers?: MapMarker[]
  /** Fired when a marker is clicked. Receives the marker index. */
  onMarkerClick?: (index: number) => void
  circles?: MapCircle[]
  polylines?: MapPolyline[]
  rects?: MapRect[]
  selectedLocation?: { latitude: number; longitude: number; label?: string }
  /** Show a persistent "DEMO DATA" watermark badge on the map. */
  demo?: boolean
  demoLabel?: string
  fitBounds?: boolean
  /** Increment to force a re-fit (used by "reset view" buttons). */
  fitToken?: number
  /** Bounds to fit to; if omitted, derived from markers/polylines/rects. */
  fitTo?: { minLat: number; minLng: number; maxLat: number; maxLng: number }
  className?: string
  zoomControlPosition?: 'topleft' | 'topright' | 'bottomleft' | 'bottomright'
}

const DARK_TILES =
  'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
const OSM_TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const OSM_ATTRIBUTION =
  '&copy; OpenStreetMap contributors &copy; CARTO'

function createCircleIcon(color: string, radius: number, coordLabel?: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      position:relative;
      width:${radius * 2}px;
      height:${radius * 2}px;
      border-radius:50%;
      background:${color}22;
      border:2px solid ${color};
      display:flex;
      align-items:center;
      justify-content:center;
      box-shadow: 0 0 12px ${color}33;
    "><div style="
      width:${Math.max(radius * 0.6, 4)}px;
      height:${Math.max(radius * 0.6, 4)}px;
      border-radius:50%;
      background:${color};
    "></div>${
      coordLabel
        ? `<div style="position:absolute;top:-14px;left:50%;transform:translateX(-50%);font-size:9px;font-weight:700;color:${color};letter-spacing:0.02em;">${coordLabel}</div>`
        : ''
    }</div>`,
    iconSize: [radius * 2, radius * 2],
    iconAnchor: [radius, radius],
  })
}

function createLocationIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="
      position:relative;
      width:26px;height:26px;
      border-radius:50%;
      background:#38bdf8;
      border:3px solid #fff;
      box-shadow:0 0 0 5px rgba(56,189,248,0.25), 0 0 22px rgba(56,189,248,0.45);
    "><div style="
      position:absolute;left:50%;top:50%;width:10px;height:10px;
      transform:translate(-50%,-50%);
      border-radius:50%;background:#fff;
    "></div></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  })
}

function createCurrentStormIcon(color: string, pulse: boolean) {
  return L.divIcon({
    className: '',
    html: `<div style="
      position:relative;
      width:30px;height:30px;
      display:flex;align-items:center;justify-content:center;
    "><div style="
      position:absolute;width:30px;height:30px;border-radius:50%;
      background:${color}22;
      ${pulse ? 'animation:stormPulse 2s ease-in-out infinite;' : ''}
    "></div><div style="
      width:14px;height:14px;border-radius:50%;
      background:${color};
      border:2px solid #fff;
      box-shadow:0 0 14px ${color}88;
    "></div></div>
    <style>@keyframes stormPulse{0%,100%{transform:scale(1);opacity:0.5}50%{transform:scale(1.45);opacity:0.15}}</style>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  })
}

function createHistoricalIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:9px;height:9px;
      border-radius:50%;
      background:${color}55;
      border:1.5px solid ${color};
    "></div>`,
    iconSize: [9, 9],
    iconAnchor: [4.5, 4.5],
  })
}

function createProjectedIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:8px;height:8px;
      border-radius:2px;
      background:${color}44;
      border:1.5px dashed ${color};
      transform:rotate(45deg);
    "></div>`,
    iconSize: [8, 8],
    iconAnchor: [4, 4],
  })
}

function createArrowHead(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
  color: string,
) {
  const angle = Math.atan2(lon2 - lon1, lat2 - lat1) * (180 / Math.PI)
  return L.divIcon({
    className: '',
    html: `<div style="
      width:0;height:0;
      border-left:5px solid transparent;
      border-right:5px solid transparent;
      border-bottom:8px solid ${color};
      transform:rotate(${90 - angle}deg);
      opacity:0.85;
      filter:drop-shadow(0 0 2px rgba(0,0,0,0.6));
    "></div>`,
    iconSize: [10, 8],
    iconAnchor: [5, 4],
  })
}

export interface LeafletMapHandle {
  resetView: () => void
}

function collectBounds(props: LeafletMapProps): L.LatLngBounds | null {
  const points: L.LatLng[] = []
  props.markers?.forEach((m) => points.push(L.latLng(m.latitude, m.longitude)))
  props.circles?.forEach((c) =>
    points.push(L.latLng(c.latitude, c.longitude)),
  )
  props.polylines?.forEach((l) =>
    l.positions.forEach((p) => points.push(L.latLng(p.latitude, p.longitude))),
  )
  props.rects?.forEach((r) =>
    points.push(
      L.latLng(r.latitude - r.spanLat / 2, r.longitude - r.spanLng / 2),
      L.latLng(r.latitude + r.spanLat / 2, r.longitude + r.spanLng / 2),
    ),
  )
  if (props.selectedLocation) {
    points.push(
      L.latLng(
        props.selectedLocation.latitude,
        props.selectedLocation.longitude,
      ),
    )
  }

  const f = props.fitTo
  if (f) {
    points.push(
      L.latLng(f.minLat, f.minLng),
      L.latLng(f.maxLat, f.maxLng),
    )
  }

  if (points.length === 0) return null
  return L.latLngBounds(points)
}

export default function LeafletMap(props: LeafletMapProps) {
  const {
    center,
    zoom = 6,
    markers = [],
    circles = [],
    polylines = [],
    rects = [],
    selectedLocation,
    demo = false,
    demoLabel = 'DEMO DATA',
    fitBounds = false,
    fitToken = 0,
    fitTo,
    className = '',
    zoomControlPosition = 'bottomright',
  } = props
  const { onMarkerClick } = props

  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstance = useRef<L.Map | null>(null)
  const markerLayers = useRef<L.Layer[]>([])
  const circleLayers = useRef<L.Layer[]>([])
  const polylineLayers = useRef<L.Layer[]>([])
  const rectLayers = useRef<L.Layer[]>([])
  const selectedLayer = useRef<L.LayerGroup | null>(null)
  const resizeObserver = useRef<ResizeObserver | null>(null)

  const fitToData = useCallback(() => {
    const map = mapInstance.current
    if (!map) return
    const bounds = collectBounds(props)
    if (bounds && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [45, 45], maxZoom: 11 })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fitToken, markers, polylines, rects, circles, selectedLocation, fitTo])

  // Create the Leaflet map once.
  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return

    const map = L.map(mapRef.current, {
      center: center ?? [20.0, 78.0],
      zoom,
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: true,
      minZoom: 4,
    })
    L.tileLayer(DARK_TILES, {
      maxZoom: 18,
      attribution: OSM_ATTRIBUTION,
    }).addTo(map)
    map.zoomControl.setPosition(zoomControlPosition)
    mapInstance.current = map
    selectedLayer.current = L.layerGroup().addTo(map)

    // Fall back to OpenStreetMap tiles if the primary tile provider ever fails
    // (network error, rate-limit, or a provider that demands an API key). This
    // permanently switches the whole map so it can never be left showing a
    // "broken / API key required" watermark.
    let fallbackApplied = false
    map.on('tileerror', () => {
      const current = mapInstance.current
      if (!current || fallbackApplied) return
      fallbackApplied = true
      current.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) {
          layer.setUrl(OSM_TILES, true)
        }
      })
    })

    // Keep the map correctly sized when containers resize (responsive layouts).
    resizeObserver.current = new ResizeObserver(() => {
      const current = mapInstance.current
      if (current) current.invalidateSize()
    })
    resizeObserver.current.observe(mapRef.current)

    return () => {
      resizeObserver.current?.disconnect()
      resizeObserver.current = null
      map.remove()
      mapInstance.current = null
      selectedLayer.current = null
      markerLayers.current = []
      circleLayers.current = []
      polylineLayers.current = []
      rectLayers.current = []
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recenter when an explicit center arrives after data load.
  useEffect(() => {
    const map = mapInstance.current
    if (!map || !center) return
    if (fitBounds) return // fitBounds effect handles framing
    map.setView(center, Math.max(map.getZoom(), 5))
  }, [center, zoom, fitBounds])

  // Markers.
  useEffect(() => {
    const map = mapInstance.current
    if (!map) return

    markerLayers.current.forEach((l) => map.removeLayer(l))
    markerLayers.current = []

    markers.forEach((m, index) => {
      const icon = m.icon ?? createCircleIcon(m.color, m.radius ?? 14)
      const marker = L.marker([m.latitude, m.longitude], { icon })
        .addTo(map)
        .bindPopup(
          `<div style="color:#0f172a;font-size:12px;font-weight:600;min-width:120px;">${m.label}</div>`,
          { className: 'dark-popup', closeButton: false },
        )
      if (onMarkerClick) {
        marker.on('click', () => onMarkerClick(index))
      }
      markerLayers.current.push(marker)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [markers])

  // Circles.
  useEffect(() => {
    const map = mapInstance.current
    if (!map) return

    circleLayers.current.forEach((l) => map.removeLayer(l))
    circleLayers.current = []

    circles.forEach((c) => {
      const circle = L.circle([c.latitude, c.longitude], {
        radius: c.radiusKm * 1000,
        color: c.color,
        fillColor: c.color,
        fillOpacity: c.fillOpacity ?? 0.08,
        weight: 1.5,
        dashArray: '4 4',
      }).addTo(map)
      circleLayers.current.push(circle)
    })
  }, [circles])

  // Polylines with optional direction arrows.
  useEffect(() => {
    const map = mapInstance.current
    if (!map) return

    polylineLayers.current.forEach((l) => map.removeLayer(l))
    polylineLayers.current = []

    polylines.forEach((line) => {
      const latlngs = line.positions.map(
        (p) => [p.latitude, p.longitude] as [number, number],
      )
      if (latlngs.length < 2) return

      const poly = L.polyline(latlngs, {
        color: line.color,
        weight: line.weight ?? 3,
        dashArray: line.dashArray,
        opacity: 0.9,
      }).addTo(map)
      if (line.label) poly.bindTooltip(line.label, { sticky: true })
      polylineLayers.current.push(poly)

      if (line.arrows && latlngs.length >= 2) {
        const step = Math.max(1, Math.floor(latlngs.length / 3))
        for (let i = 0; i < latlngs.length - 1; i += step) {
          const next = i + 1 < latlngs.length ? i + 1 : i
          if (next === i) continue
          const arrowIcon = createArrowHead(
            latlngs[i][0], latlngs[i][1],
            latlngs[next][0], latlngs[next][1],
            line.color,
          )
          const arrowMarker = L.marker(
            [(latlngs[i][0] + latlngs[next][0]) / 2, (latlngs[i][1] + latlngs[next][1]) / 2],
            { icon: arrowIcon, interactive: false },
          ).addTo(map)
          polylineLayers.current.push(arrowMarker)
        }
      }
    })
  }, [polylines])

  // Rectangles (risk grid cells).
  useEffect(() => {
    const map = mapInstance.current
    if (!map) return

    rectLayers.current.forEach((l) => map.removeLayer(l))
    rectLayers.current = []

    rects.forEach((r) => {
      const bounds: L.LatLngBoundsExpression = [
        [r.latitude - r.spanLat / 2, r.longitude - r.spanLng / 2],
        [r.latitude + r.spanLat / 2, r.longitude + r.spanLng / 2],
      ]
      const rect = L.rectangle(bounds, {
        color: r.color,
        weight: 1.2,
        fillColor: r.color,
        fillOpacity: r.fillOpacity ?? 0.28,
      }).addTo(map)
      if (r.label) rect.bindTooltip(r.label, { sticky: true })
      rectLayers.current.push(rect)
    })
  }, [rects])

  // Selected location marker.
  useEffect(() => {
    const layer = selectedLayer.current
    if (!layer) return
    layer.clearLayers()
    if (selectedLocation) {
      L.marker([selectedLocation.latitude, selectedLocation.longitude], {
        icon: createLocationIcon(),
        zIndexOffset: 1000,
      })
        .addTo(layer)
        .bindPopup(
          `<div style="color:#0f172a;font-size:12px;font-weight:700;">${
            selectedLocation.label ?? 'Selected Location'
          }</div>`,
          { closeButton: false },
        )
    }
  }, [selectedLocation])

  // Demo watermark badge (rendered as an overlay above the map container).
  const demoOverlay = demo ? (
    <div className="pointer-events-none absolute left-1/2 top-2.5 z-[500] -translate-x-1/2">
      <span
        className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/60 bg-slate-950/85 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-amber-300 shadow-lg backdrop-blur"
        role="status"
        aria-label={demoLabel}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400 shadow-[0_0_8px_#fbbf24]" />
        {demoLabel}
      </span>
    </div>
  ) : null

  // Fit bounds the first time data is ready, and every time fitToken changes.
  useEffect(() => {
    if (!fitBounds) return
    fitToData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fitBounds, fitToken])

  return (
    <div
      ref={mapRef}
      className={`relative h-full w-full ${className}`}
      style={{ minHeight: '300px' }}
    >
      {demoOverlay}
    </div>
  )
}

export {
  createLocationIcon,
  createCurrentStormIcon,
  createHistoricalIcon,
  createProjectedIcon,
  createCircleIcon,
}