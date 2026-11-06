
import { useState } from 'react'
import { Flame, Loader2, RotateCcw, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { api, type AlgerianPrediction } from '../lib/api'

const features = [
  { name: 'Temperature', label: 'Temperature', unit: '°C' },
  { name: 'Ws', label: 'Wind Speed', unit: 'km/h' },
  { name: 'Rain', label: 'Rainfall', unit: 'mm' },
  { name: 'RH', label: 'Relative Humidity', unit: '%' },
  { name: 'FFMC', label: 'FFMC', unit: '' },
  { name: 'DMC', label: 'DMC', unit: '' },
  { name: 'DC', label: 'DC', unit: '' },
  { name: 'ISI', label: 'ISI', unit: '' },
  { name: 'BUI', label: 'BUI', unit: '' },
  { name: 'FWI', label: 'FWI', unit: '' },
] as const

type FormValues = Record<string, string>

const initialValues: FormValues = Object.fromEntries(
  features.map((feature) => [feature.name, ''])
)

export default function PredictionLab() {
  const [values, setValues] = useState<FormValues>(initialValues)
  const [result, setResult] = useState<AlgerianPrediction | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (name: string, value: string) => {
    setValues((previous) => ({ ...previous, [name]: value }))
  }

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

    if (missing.length > 0) {
      setError(`Please enter: ${missing.map((item) => item.label).join(', ')}`)
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
      const prediction = await api.predictAlgerian(payload)
      setResult(prediction)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed. Check backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const isFire = result?.prediction === 1

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 text-orange-400 text-sm font-medium mb-2">
          <Flame size={16} />
          AI PREDICTION ENGINE
        </div>
        <h1 className="text-2xl font-semibold text-white">AI Risk Prediction Lab</h1>
        <p className="text-sm text-slate-400 mt-1">
          Evaluate fire occurrence using the trained Algerian forest-fire classification model.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.3fr_0.7fr] gap-6">
        <form onSubmit={handlePredict} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-5">
          <div>
            <h2 className="text-base font-semibold text-white">Environmental Parameters</h2>
            <p className="text-xs text-slate-500 mt-1">
              Enter all ten features required by the model.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {features.map((feature) => (
              <label key={feature.name} className="block">
                <span className="text-sm text-slate-300">{feature.label}</span>
                <div className="relative mt-2">
                  <input
                    type="number"
                    step="any"
                    value={values[feature.name]}
                    onChange={(event) => handleChange(feature.name, event.target.value)}
                    placeholder={`Enter ${feature.label.toLowerCase()}`}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-orange-500"
                  />
                  {feature.unit && (
                    <span className="absolute right-3 top-3 text-xs text-slate-500">
                      {feature.unit}
                    </span>
                  )}
                </div>
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
              className="flex items-center justify-center gap-2 rounded-lg bg-orange-500 px-5 py-3 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-60"
            >
              {loading ? <Loader2 size={17} className="animate-spin" /> : <Flame size={17} />}
              {loading ? 'Analyzing...' : 'Run Prediction'}
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
          <h2 className="text-base font-semibold text-white">Prediction Results</h2>
          <p className="text-xs text-slate-500 mt-1">Model inference output</p>

          {!result ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center text-center">
              <div className="rounded-full bg-slate-800 p-5 mb-4">
                <Flame size={30} className="text-slate-500" />
              </div>
              <p className="text-sm font-medium text-slate-300">No prediction yet</p>
              <p className="text-xs text-slate-500 mt-2 max-w-[220px]">
                Enter environmental parameters and run the model to see the result.
              </p>
            </div>
          ) : (
            <div className="space-y-5 mt-6">
              <div className={`rounded-xl p-5 border ${isFire ? 'border-orange-700/50 bg-orange-950/30' : 'border-emerald-700/50 bg-emerald-950/30'}`}>
                <div className="flex items-center gap-2 mb-3">
                  {isFire ? <Flame className="text-orange-400" /> : <CheckCircle2 className="text-emerald-400" />}
                  <span className={`text-sm font-semibold ${isFire ? 'text-orange-300' : 'text-emerald-300'}`}>
                    {result.label}
                  </span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {(result.probability_fire * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-slate-400 mt-1">Predicted fire probability</p>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-400">Fire probability</span>
                  <span className="text-white">{(result.probability_fire * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-orange-500"
                    style={{ width: `${Math.max(0, Math.min(100, result.probability_fire * 100))}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-3 text-sm">
                <span className="text-slate-400">Risk Level</span>
                <span className="text-white font-medium">{result.risk_level}</span>
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
