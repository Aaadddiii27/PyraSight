import { useEffect, useState } from 'react'
import { Database, HeartPulse, RefreshCw, Server, Satellite, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { api, type FIRMSStatusResponse, type ModelInfo } from '../lib/api'

type Health = { status: string; version: string; models: Record<string, string>; data_mode: string }

export default function SettingsDataSources() {
  const [health,setHealth] = useState<Health|null>(null); const [firms,setFirms] = useState<FIRMSStatusResponse|null>(null); const [models,setModels] = useState<ModelInfo[]>([]); const [loading,setLoading] = useState(true); const [error,setError] = useState('')
  async function load() {
    setLoading(true); setError('')
    const results = await Promise.allSettled([api.health(),api.firmsStatus(),api.models()])
    if(results[0].status==='fulfilled') setHealth(results[0].value)
    if(results[1].status==='fulfilled') setFirms(results[1].value)
    if(results[2].status==='fulfilled') setModels(results[2].value)
    if(results.every(x=>x.status==='rejected')) setError('Backend status endpoints could not be reached.')
    setLoading(false)
  }
  useEffect(()=>{void load()},[])
  const healthy = ['ok','healthy'].includes((health?.status ?? '').toLowerCase())
  return <div className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="mb-2 flex items-center gap-2 text-sm font-medium text-orange-400"><Database size={16}/> PLATFORM CONFIGURATION</p><h1 className="text-2xl font-semibold text-white">Settings & Data Sources</h1><p className="mt-1 text-sm text-slate-400">Inspect backend health, satellite data availability and registered model status.</p></div><button onClick={()=>void load()} disabled={loading} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"><RefreshCw size={15} className={loading?'animate-spin':''}/> Refresh status</button></div>
    {error && <div className="flex gap-2 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300"><AlertTriangle size={17}/>{error}</div>}
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><div className="mb-4 flex items-center gap-2"><HeartPulse size={18} className="text-emerald-400"/><h2 className="font-semibold text-white">Backend health</h2></div><div className="grid gap-3 sm:grid-cols-3"><div className="rounded-lg bg-slate-950 p-4"><p className="text-xs text-slate-500">Service status</p><p className={`mt-2 flex items-center gap-2 text-sm ${healthy?'text-emerald-400':'text-amber-400'}`}>{health?<><CheckCircle2 size={15}/>{health.status}</>:loading?'Checking...':'Unavailable'}</p></div><div className="rounded-lg bg-slate-950 p-4"><p className="text-xs text-slate-500">API version</p><p className="mt-2 text-sm text-white">{health?.version??'—'}</p></div><div className="rounded-lg bg-slate-950 p-4"><p className="text-xs text-slate-500">Data mode</p><p className="mt-2 text-sm text-white">{health?.data_mode??firms?.data_mode??'—'}</p></div></div></section>
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><div className="mb-4 flex items-center gap-2"><Satellite size={18} className="text-blue-400"/><h2 className="font-semibold text-white">NASA FIRMS data source</h2></div><div className="mb-4 grid gap-3 sm:grid-cols-2"><div className="rounded-lg bg-slate-950 p-4"><p className="text-xs text-slate-500">Total loaded detections</p><p className="mt-2 text-xl font-semibold text-white">{firms?.total_detections?.toLocaleString()??'—'}</p></div><div className="rounded-lg bg-slate-950 p-4"><p className="text-xs text-slate-500">Last loaded</p><p className="mt-2 text-sm text-white">{firms?.last_loaded?new Date(firms.last_loaded).toLocaleString():'Not reported'}</p></div></div><h3 className="mb-2 text-xs font-medium text-slate-400">AVAILABLE FILES</h3>{firms?.files_available && Object.keys(firms.files_available).length?<div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{Object.entries(firms.files_available).map(([name,available])=><div key={name} className="flex items-center justify-between rounded-lg border border-slate-800 p-3"><span className="text-sm text-slate-300">{name}</span><span className={`text-xs ${available?'text-emerald-400':'text-slate-500'}`}>{available?'Available':'Unavailable'}</span></div>)}</div>:<p className="text-xs text-slate-500">No per-file availability details returned.</p>}</section>
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><div className="mb-4 flex items-center gap-2"><Server size={18} className="text-purple-400"/><h2 className="font-semibold text-white">Model services</h2></div>{models.length?<div className="space-y-2">{models.map(model=><div key={model.model_id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 p-3"><div><p className="text-sm text-white">{model.model_id}</p><p className="text-xs text-slate-500">{model.model_type??'Model'} · {model.dataset??'Dataset not specified'}</p></div><span className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-300">{model.status}</span></div>)}</div>:<p className="text-sm text-slate-500">{loading?'Loading model registry...':'No model information available.'}</p>}</section>
    <p className="text-xs text-slate-600">Read-only status view. This page does not modify environment variables, credentials, data files or model artifacts.</p>
  </div>
}
