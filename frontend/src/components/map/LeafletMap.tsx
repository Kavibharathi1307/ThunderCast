import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export interface MapMarker {
  latitude: number
  longitude: number
  label: string
  color: string
  radius?: number
}

interface LeafletMapProps {
  center: [number, number]
  zoom: number
  markers?: MapMarker[]
  className?: string
}

const DEFAULT_STYLE = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'

function createCircleIcon(color: string, radius: number) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:${radius * 2}px;
      height:${radius * 2}px;
      border-radius:50%;
      background:${color}33;
      border:2px solid ${color};
      display:flex;
      align-items:center;
      justify-content:center;
    "><div style="
      width:${radius}px;
      height:${radius}px;
      border-radius:50%;
      background:${color};
      opacity:0.8;
    "></div></div>`,
    iconSize: [radius * 2, radius * 2],
    iconAnchor: [radius, radius],
  })
}

export default function LeafletMap({ center, zoom, markers = [], className = '' }: LeafletMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstance = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return

    const map = L.map(mapRef.current, {
      center,
      zoom,
      zoomControl: true,
      attributionControl: false,
    })

    L.tileLayer(DEFAULT_STYLE, {
      maxZoom: 18,
    }).addTo(map)

    mapInstance.current = map

    return () => {
      map.remove()
      mapInstance.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const map = mapInstance.current
    if (!map) return
    map.setView(center, zoom)
  }, [center, zoom])

  useEffect(() => {
    const map = mapInstance.current
    if (!map) return

    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.CircleMarker) {
        map.removeLayer(layer)
      }
    })

    markers.forEach((m) => {
      const icon = createCircleIcon(m.color, m.radius ?? 14)
      L.marker([m.latitude, m.longitude], { icon })
        .addTo(map)
        .bindPopup(`<div style="color:#1e293b;font-size:13px;font-weight:600;">${m.label}</div>`)
    })
  }, [markers])

  return (
    <div
      ref={mapRef}
      className={`h-full w-full ${className}`}
      style={{ minHeight: '400px' }}
    />
  )
}
