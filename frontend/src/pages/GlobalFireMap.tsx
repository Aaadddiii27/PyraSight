
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import maplibregl, {
  type GeoJSONSource,
  type Map as MapLibreMap,
} from 'maplibre-gl'

import { api, type FIRMSDetection } from '../lib/api'

import 'maplibre-gl/dist/maplibre-gl.css'

const MAP_STYLE = 'https://demotiles.maplibre.org/style.json'

export default function GlobalFireMap() {
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<MapLibreMap | null>(null)

  const [satellite, setSatellite] = useState('')
  const [confidence, setConfidence] = useState('')
  const [selected, setSelected] = useState<FIRMSDetection | null>(null)
  const [mapReady, setMapReady] = useState(false)

  const queryParams = useMemo(() => {
    const params: Record<string, string> = { limit: '5000' }

    if (satellite) params.satellite = satellite
    if (confidence) params.confidence = confidence

    return params
  }, [satellite, confidence])

  const detectionsQuery = useQuery({
    queryKey: ['map-detections', queryParams],
    queryFn: () => api.firmsDetections(queryParams),
    retry: 1,
  })

  const detections = detectionsQuery.data?.detections ?? []

  // --------------------------------------------------
  // Create map once
  // --------------------------------------------------

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [15, 20],
      zoom: 1.5,
      attributionControl: {
        compact: true,
      },
    })

    mapRef.current = map

    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left')

    map.on('load', () => {
      // Create the GeoJSON source
      if (!map.getSource('fire-detections')) {
        map.addSource('fire-detections', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })
      }

      // Create the detection marker layer
      if (!map.getLayer('fire-points')) {
        map.addLayer({
          id: 'fire-points',
          type: 'circle',
          source: 'fire-detections',
          paint: {
            'circle-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              1, 3,
              7, 6,
              12, 9,
            ],
            'circle-color': [
              'match',
              ['get', 'confidence'],
              'high', '#fb4b32',
              'nominal', '#f59e0b',
              'low', '#facc15',
              '#f97316',
            ],
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff',
            'circle-opacity': 0.85,
          },
        })
      }

      // Tell React that the map source and layer are ready
      setMapReady(true)

      // Handle detection marker clicks
      map.on('click', 'fire-points', event => {
        const feature = event.features?.[0]

        if (!feature) return

        const properties = feature.properties
        if (!properties) return

        const coordinates = (
          feature.geometry as GeoJSON.Point
        ).coordinates

        setSelected({
          latitude: coordinates[1],
          longitude: coordinates[0],
          satellite: properties.satellite ?? '',
          confidence: properties.confidence ?? '',
          acq_date: properties.acq_date ?? '',
          acq_time: properties.acq_time ?? '',
          frp: properties.frp == null ? null : Number(properties.frp),
          bright_ti4:
            properties.bright_ti4 == null
              ? null
              : Number(properties.bright_ti4),
          bright_ti5:
            properties.bright_ti5 == null
              ? null
              : Number(properties.bright_ti5),
          scan: properties.scan == null ? null : Number(properties.scan),
          track: properties.track == null ? null : Number(properties.track),
          version: properties.version ?? '',
          daynight: properties.daynight ?? '',
          product: properties.product ?? '',
        })

        map.flyTo({
          center: [coordinates[0], coordinates[1]],
          zoom: Math.max(map.getZoom(), 5),
          duration: 700,
        })
      })

      map.on('mouseenter', 'fire-points', () => {
        map.getCanvas().style.cursor = 'pointer'
      })

      map.on('mouseleave', 'fire-points', () => {
        map.getCanvas().style.cursor = ''
      })
    })

    return () => {
      map.remove()
      mapRef.current = null
      setMapReady(false)
    }
  }, [])

  // --------------------------------------------------
  // Update detection data after the map is ready
  // --------------------------------------------------

  useEffect(() => {
    const map = mapRef.current

    if (!map || !mapReady) return

    const source = map.getSource(
      'fire-detections'
    ) as GeoJSONSource | undefined

    if (!source) {
      console.warn('[GlobalFireMap] Detection source not found')
      return
    }

    // Validate coordinates before creating map features
    const validDetections = detections.filter(detection => {
      const latitude = Number(detection.latitude)
      const longitude = Number(detection.longitude)

      return (
        detection.latitude != null &&
        detection.longitude != null &&
        Number.isFinite(latitude) &&
        Number.isFinite(longitude) &&
        latitude >= -90 &&
        latitude <= 90 &&
        longitude >= -180 &&
        longitude <= 180
      )
    })

    // Convert API detections into GeoJSON features
    const features = validDetections.map(detection => ({
      type: 'Feature' as const,
      geometry: {
        type: 'Point' as const,
        coordinates: [
          Number(detection.longitude),
          Number(detection.latitude),
        ],
      },
      properties: {
        satellite: detection.satellite,
        confidence: detection.confidence?.toLowerCase(),
        acq_date: detection.acq_date,
        acq_time: detection.acq_time,
        frp: detection.frp,
        bright_ti4: detection.bright_ti4,
        bright_ti5: detection.bright_ti5,
        scan: detection.scan,
        track: detection.track,
        version: detection.version,
        daynight: detection.daynight,
        product: detection.product,
      },
    }))

    // Update the map source
    source.setData({
      type: 'FeatureCollection',
      features,
    })

    console.log(
      `[GlobalFireMap] Rendered ${features.length} detections`
    )

    // Automatically fit the map to the available detections
    if (features.length > 0) {
      const bounds = new maplibregl.LngLatBounds()

      features.forEach(feature => {
        const coordinates = feature.geometry.coordinates as [
          number,
          number,
        ]

        bounds.extend(coordinates)
      })

      map.fitBounds(bounds, {
        padding: 60,
        maxZoom: 5,
        duration: 1000,
      })
    }
  }, [detections, mapReady])

  // --------------------------------------------------
  // Clear filters
  // --------------------------------------------------

  const clearFilters = () => {
    setSatellite('')
    setConfidence('')
    setSelected(null)
  }

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="space-y-5">

      {/* Map header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium uppercase tracking-wider text-pyra-muted">
              Satellite monitoring
            </span>
          </div>

          <p className="mt-2 text-sm text-pyra-muted">
            Explore thermal detections recorded by NASA VIIRS satellites.
          </p>
        </div>

        <button
          onClick={() => detectionsQuery.refetch()}
          disabled={detectionsQuery.isFetching}
          className="rounded-lg border border-pyra-border bg-pyra-surface px-4 py-2 text-xs text-white hover:bg-pyra-hover disabled:opacity-50"
        >
          {detectionsQuery.isFetching
            ? 'Refreshing...'
            : 'Refresh detections'}
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl border border-pyra-border bg-pyra-surface p-4">

        <div className="min-w-40 flex-1">
          <label className="mb-2 block text-xs text-pyra-muted">
            Satellite
          </label>

          <select
            value={satellite}
            onChange={event => {
              setSatellite(event.target.value)
              setSelected(null)
            }}
            className="w-full rounded-lg border border-pyra-border bg-pyra-card px-3 py-2.5 text-sm text-white outline-none focus:border-orange-400"
          >
            <option value="">All satellites</option>
            <option value="J1_VIIRS_C2">NOAA-20</option>
            <option value="J2_VIIRS_C2">NOAA-21</option>
            <option value="SUOMI_VIIRS_C2">SNPP</option>
          </select>
        </div>

        <div className="min-w-40 flex-1">
          <label className="mb-2 block text-xs text-pyra-muted">
            Confidence
          </label>

          <select
            value={confidence}
            onChange={event => {
              setConfidence(event.target.value)
              setSelected(null)
            }}
            className="w-full rounded-lg border border-pyra-border bg-pyra-card px-3 py-2.5 text-sm text-white outline-none focus:border-orange-400"
          >
            <option value="">All confidence levels</option>
            <option value="high">High</option>
            <option value="nominal">Nominal</option>
            <option value="low">Low</option>
          </select>
        </div>

        <button
          onClick={clearFilters}
          className="rounded-lg border border-pyra-border px-4 py-2.5 text-xs text-pyra-muted hover:bg-pyra-hover hover:text-white"
        >
          Clear filters
        </button>
      </div>

      {/* Map and details */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">

        {/* Map */}
        <div className="relative overflow-hidden rounded-xl border border-pyra-border bg-pyra-surface xl:col-span-3">

          <div
            ref={mapContainer}
            className="h-[520px] w-full"
          />

          {/* Detection count */}
          <div className="absolute left-4 top-4 z-10 rounded-lg border border-pyra-border bg-pyra-bg/90 px-3 py-2 backdrop-blur">
            <p className="text-[10px] uppercase tracking-wider text-pyra-muted">
              Visible detection records
            </p>

            <p className="mt-1 text-lg font-semibold text-white">
              {detectionsQuery.isLoading
                ? '...'
                : detectionsQuery.isError
                  ? 'Unavailable'
                  : detections.length.toLocaleString()}
            </p>
          </div>

          {/* Confidence legend */}
          <div className="absolute bottom-5 left-4 z-10 rounded-lg border border-pyra-border bg-pyra-bg/90 p-3 backdrop-blur">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-pyra-muted">
              Confidence legend
            </p>

            <div className="space-y-1.5 text-xs text-white">
              <p>
                <span className="mr-2 text-red-400">●</span>
                High
              </p>
              <p>
                <span className="mr-2 text-amber-400">●</span>
                Nominal
              </p>
              <p>
                <span className="mr-2 text-yellow-300">●</span>
                Low
              </p>
            </div>
          </div>

          {/* API error */}
          {detectionsQuery.isError && (
            <div className="absolute bottom-5 right-4 z-10 rounded-lg border border-red-500/30 bg-pyra-bg/95 p-3 text-xs text-red-300">
              Could not load FIRMS records. Check backend availability.
            </div>
          )}
        </div>

        {/* Selected detection details */}
        <aside className="rounded-xl border border-pyra-border bg-pyra-surface p-5">

          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">
              Detection Details
            </h2>

            {selected && (
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-pyra-muted hover:text-white"
              >
                Clear
              </button>
            )}
          </div>

          {selected ? (
            <div className="space-y-4">

              <div>
                <p className="text-xs text-pyra-muted">
                  Confidence
                </p>
                <p className="mt-1 text-lg font-semibold capitalize text-orange-400">
                  {selected.confidence}
                </p>
              </div>

              {[
                ['Satellite', selected.satellite],
                ['Product', selected.product],
                ['Acquisition date', selected.acq_date],
                ['Acquisition time', selected.acq_time],
                ['Latitude', selected.latitude.toFixed(4)],
                ['Longitude', selected.longitude.toFixed(4)],
                ['Fire Radiative Power', selected.frp ?? 'Unavailable'],
                [
                  'Brightness temperature',
                  selected.bright_ti4 ?? 'Unavailable',
                ],
                ['Day / Night', selected.daynight],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="flex justify-between gap-3 border-b border-pyra-border pb-3"
                >
                  <span className="text-xs text-pyra-muted">
                    {label}
                  </span>

                  <span className="max-w-[55%] break-words text-right text-xs text-white">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex min-h-64 flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500/10 text-orange-400">
                <span className="text-xl">⌖</span>
              </div>

              <p className="text-sm font-medium text-white">
                No detection selected
              </p>

              <p className="mt-2 text-xs leading-relaxed text-pyra-muted">
                Select a point on the map to inspect its satellite
                observation details.
              </p>
            </div>
          )}
        </aside>
      </div>

      {/* Source information */}
      <div className="rounded-lg border border-pyra-border bg-pyra-card px-4 py-3">
        <p className="text-[10px] leading-relaxed text-pyra-muted">
          Source: {detectionsQuery.data?.source ?? 'NASA FIRMS VIIRS'}.
          {' '}Data mode: {detectionsQuery.data?.data_mode ?? 'Not reported'}.
          {' '}Satellite thermal detections are not necessarily confirmed wildfires.
          {' '}Map tiles are provided by the MapLibre demo tile service.
        </p>
      </div>
    </div>
  )
}
