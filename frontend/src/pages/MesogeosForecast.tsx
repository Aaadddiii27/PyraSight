
import { useState } from 'react'
import { Activity, AlertTriangle, CheckCircle2, Loader2, RotateCcw } from 'lucide-react'
import { api, type MesogeosPrediction } from '../lib/api'

const features = [
  { name: 'aspect', label: 'Aspect' },
  { name: 'curvature', label: 'Curvature' },
  { name: 'd2m', label: 'Dew Point Temperature' },
  { name: 'dem', label: 'Elevation (DEM)' },
  { name: 'lai', label: 'Leaf Area Index' },
  { name: 'lst_day', label: 'Land Surface Temperature (Day)' },
  { name: 'lst_night', label: 'Land Surface Temperature (Night)' },
  { name: 'ndvi', label: 'Vegetation Index (NDVI)' },
  { name: 'rh', label: 'Relative Humidity' },
  { name: 'roads_distance', label: 'Distance from Roads' },
  { name: 'slope', label: 'Terrain Slope' },
  { name: 'smi', label: 'Soil Moisture Index' },
  { name: 'sp', label: 'Surface Pressure' },
  { name: 'ssrd', label: 'Solar Radiation' },
  { name: 't2m', label: 'Temperature (2m)' },
  { name: 'tp', label: 'Total Precipitation' },
  { name: 'wind_direction', label: 'Wind Direction' },
  { name: 'wind_speed', label: 'Wind Speed' },
  { name: 'lc_agriculture', label: 'Land Cover: Agriculture' },
  { name: 'lc_forest', label: 'Land Cover: Forest' },
  { name: 'lc_grassland', label: 'Land Cover: Grassland' },
  { name: 'lc_settlement', label: 'Land Cover: Settlement' },
  { name: 'lc_shrubland', label: 'Land Cover: Shrubland' },
  { name: 'lc_sparse_vegetation', label: 'Land Cover: Sparse Vegetation' },
  { name: 'lc_water_bodies', label: 'Land Cover: Water Bodies' },
  { name: 'lc_wetland', label: 'Land Cover: Wetland' },
  { name: 'population', label: 'Population' },
] as const

type FormValues = Record<string, string>

const initialValues: FormValues = Object.fromEntries(
  features.map((feature) => [feature.name, ''])
)

export default function MesogeosForecast() {
  const [values, setValues] = useState<FormValues>(initialValues)
  const [result, setResult] = useState<MesogeosPrediction | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleReset = () => {
    setValues(initialValues)
    setResult(null)
    setError('')
  }

  const handlePredict = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setResult(null)

    const missing = features.filter(
      (feature) => values[feature.name].trim() === ''
    )

    if (missing.length) {
      setError(`Please enter all features. Missing: ${missing.map((item) => item.name).join(', ')}`)
      return
    }

    const payload: Record<string, number> = {}

    for (const feature of features) {
      const value = Number(values[feature.name])

      if (!Number.isFinite(value)) {
        setError(`Invalid value for ${feature.label}`)
        return
      }

      payload[feature.name] = value
    }

    setLoading(true)

    try {
      const prediction = await api.predictMesogeos(payload)
      setResult(prediction)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed. Check backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const isDanger = result?.prediction === 1

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 text-orange-400 text-sm font-medium mb-2">
          <Activity size={16} />
          GEOSPATIAL HAZARD INTELLIGENCE
        </div>
        <h1 className="text-2xl font-semibold text-white">Mesogeos Hazard Forecast</h1>
        <p className="text-sm text-slate-400 mt-1">
          Evaluate environmental fire-danger conditions using the Mesogeos XGBoost model.
        </p>
      </div>

      <div className="rounded-xl border border-amber-800/40 bg-amber-950/20 p-4">
        <div className="flex gap-2 text-amber-300 text-sm font-medium">
          <AlertTriangle size={17} />
          Input data requirement
        </div>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
          This model requires 27 environmental and geospatial features. Use values
          from a compatible Mesogeos data sample. Do not enter arbitrary values:
          the model output is meaningful only when inputs use the same units,
          encoding and preprocessing as the training data.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.3fr_0.7fr] gap-6">
        <form onSubmit={handlePredict} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-5">
          <div>
            <h2 className="text-base font-semibold text-white">Environmental & Geospatial Features</h2>
            <p className="text-xs text-slate-500 mt-1">All 27 model features are required.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {features.map((feature) => (
              <label key={feature.name} className="block">
                <span className="text-sm text-slate-300">{feature.label}</span>
                <input
                  type="number"
                  step="any"
                  value={values[feature.name]}
                  onChange={(event) =>
                    setValues((previous) => ({
                      ...previous,
                      [feature.name]: event.target.value,
                    }))
                  }
                  placeholder={`Enter ${feature.name}`}
                  className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-orange-500"
                />
              </label>
            ))}
          </div>

          {error && (
            <div className="flex gap-2 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300">
              <AlertTriangle size={17} className="shrink-0" />
              {error}
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-orange-500 px-5 py-3 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-60"
            >
              {loading ? <Loader2 size={17} className="animate-spin" /> : <Activity size={17} />}
              {loading ? 'Analyzing...' : 'Run Hazard Analysis'}
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-3 text-sm text-slate-300 hover:bg-slate-800"
            >
              <RotateCcw size={16} />
              Reset
            </button>
          </div>
        </form>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-base font-semibold text-white">Hazard Assessment</h2>
          <p className="text-xs text-slate-500 mt-1">Mesogeos model inference</p>

          {!result ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center text-center">
              <div className="rounded-full bg-slate-800 p-5 mb-4">
                <Activity size={30} className="text-slate-500" />
              </div>
              <p className="text-sm font-medium text-slate-300">Awaiting assessment</p>
              <p className="text-xs text-slate-500 mt-2 max-w-[220px]">
                Submit compatible environmental data to receive a hazard assessment.
              </p>
            </div>
          ) : (
            <div className="space-y-5 mt-6">
              <div className={`rounded-xl border p-5 ${isDanger ? 'border-orange-700/50 bg-orange-950/30' : 'border-emerald-700/50 bg-emerald-950/30'}`}>
                <div className="flex items-center gap-2 mb-3">
                  {isDanger
                    ? <AlertTriangle className="text-orange-400" />
                    : <CheckCircle2 className="text-emerald-400" />}
                  <span className={`text-sm font-semibold ${isDanger ? 'text-orange-300' : 'text-emerald-300'}`}>
                    {result.label}
                  </span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {(result.probability_danger * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-slate-400 mt-1">Fire-danger probability</p>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-3 text-sm">
                <span className="text-slate-400">Danger Level</span>
                <span className="text-white font-medium">{result.danger_level}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-3 text-sm">
                <span className="text-slate-400">Model</span>
                <span className="text-white">{result.model_type}</span>
              </div>

              {result.disclaimer && (
                <p className="text-xs leading-relaxed text-slate-500">{result.disclaimer}</p>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
