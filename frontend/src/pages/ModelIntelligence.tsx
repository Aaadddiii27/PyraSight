import { useEffect, useState } from 'react'
import { Activity, BrainCircuit, RefreshCw, ShieldCheck, AlertTriangle } from 'lucide-react'
import { api, type ModelInfo } from '../lib/api'

type Detail = { metrics?: Record<string, unknown>; explanation?: { model_id: string; method: string; feature_importance: Record<string, number> }; error?: string }
const pretty = (v: unknown) => v == null ? '—' : typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 4 }) : typeof v === 'string' || typeof v === 'boolean' ? String(v) : JSON.stringify(v)

export default function ModelIntelligence() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [details, setDetails] = useState<Record<string, Detail>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true); setError('')
    try {
      const list = await api.models(); setModels(list)
      const entries = await Promise.all(list.map(async model => {
        const [metrics, explanation] = await Promise.allSettled([api.modelMetrics(model.model_id), api.modelExplanations(model.model_id)])
        return [model.model_id, { ...(metrics.status === 'fulfilled' ? { metrics: metrics.value } : {}), ...(explanation.status === 'fulfilled' ? { explanation: explanation.value } : {}), ...(metrics.status === 'rejected' && explanation.status === 'rejected' ? { error: 'Metrics and explanations unavailable.' } : {}) }] as const
      }))
      setDetails(Object.fromEntries(entries))
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not load model registry.') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])

  return <div className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="mb-2 flex items-center gap-2 text-sm font-medium text-orange-400"><BrainCircuit size={16}/> MODEL GOVERNANCE</p><h1 className="text-2xl font-semibold text-white">Model Intelligence</h1><p className="mt-1 text-sm text-slate-400">Inspect registered models, evaluation metrics and available feature explanations.</p></div><button onClick={() => void load()} disabled={loading} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"><RefreshCw size={15} className={loading ? 'animate-spin' : ''}/> Refresh</button></div>
    {error && <div className="flex gap-2 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300"><AlertTriangle size={17}/>{error}</div>}
    <div className="grid gap-4 sm:grid-cols-3"><div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><p className="text-sm text-slate-400">Registered models</p><p className="mt-3 text-2xl font-semibold text-white">{loading ? '...' : models.length}</p></div><div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><p className="text-sm text-slate-400">Ready / loaded</p><p className="mt-3 text-2xl font-semibold text-emerald-400">{loading ? '...' : models.filter(m => ['available','loaded','ready'].includes(m.status.toLowerCase())).length}</p></div><div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><p className="text-sm text-slate-400">With evaluation data</p><p className="mt-3 text-2xl font-semibold text-white">{loading ? '...' : models.filter(m => m.evaluation && Object.keys(m.evaluation).length > 0).length}</p></div></div>
    {loading && <p className="py-10 text-center text-sm text-slate-500">Loading model registry...</p>}
    {!loading && models.length === 0 && !error && <p className="rounded-xl border border-slate-800 p-8 text-center text-sm text-slate-500">No models registered by the backend.</p>}
    <div className="space-y-4">{models.map(model => {
      const detail = details[model.model_id]; const importance = Object.entries(detail?.explanation?.feature_importance ?? {}).sort((a,b) => b[1]-a[1]).slice(0,8); const metrics = detail?.metrics ?? model.evaluation ?? {}; const max = Math.max(...importance.map(x => x[1]), 0.000001)
      return <section key={model.model_id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-center gap-3"><div className="rounded-lg bg-slate-800 p-3"><BrainCircuit className="text-orange-400" size={21}/></div><div><h2 className="font-semibold text-white">{model.model_id}</h2><p className="text-xs text-slate-500">{model.model_type ?? 'Model type not reported'} · {model.dataset ?? 'Dataset not reported'}</p></div></div><span className="flex items-center gap-1 rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300"><ShieldCheck size={13}/>{model.status}</span></div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['Training samples',model.n_train],['Test samples',model.n_test],['Target',model.target],['Geographic scope',model.geographic_scope]].map(([k,v]) => <div key={String(k)} className="rounded-lg bg-slate-950 p-3"><p className="text-xs text-slate-500">{k}</p><p className="mt-1 text-sm text-white">{pretty(v)}</p></div>)}</div>
        <div className="mt-5"><h3 className="mb-2 flex items-center gap-2 text-sm font-medium text-white"><Activity size={15} className="text-blue-400"/> Evaluation metrics</h3>{Object.keys(metrics).length ? <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(metrics).map(([k,v]) => <div key={k} className="rounded-lg border border-slate-800 p-3"><p className="text-xs text-slate-500">{k.replace(/_/g, ' ')}</p><p className="mt-1 break-all text-sm text-white">{pretty(v)}</p></div>)}</div> : <p className="text-xs text-slate-500">No evaluation metrics returned.</p>}</div>
        <div className="mt-5"><h3 className="mb-2 text-sm font-medium text-white">Feature importance</h3>{importance.length ? <div className="space-y-3">{importance.map(([name,value]) => <div key={name}><div className="mb-1 flex justify-between text-xs"><span className="text-slate-300">{name}</span><span className="text-slate-400">{pretty(value)}</span></div><div className="h-1.5 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-orange-500" style={{width:`${Math.max(0,Math.min(100,value/max*100))}%`}}/></div></div>)}</div> : <p className="text-xs text-slate-500">{detail?.explanation?.method ? `Explanation method: ${detail.explanation.method}.` : 'Feature importance not available.'}</p>}</div>
        {detail?.error && <p className="mt-4 text-xs text-amber-400">{detail.error}</p>}{model.features?.length ? <p className="mt-4 text-xs text-slate-500">Input features: {model.features.join(', ')}</p> : null}
      </section>
    })}</div>
    <p className="text-xs text-slate-600">Metrics and explanations are displayed as returned by the backend; evaluation methodology should be reviewed independently before treating them as validated performance.</p>
  </div>
}
