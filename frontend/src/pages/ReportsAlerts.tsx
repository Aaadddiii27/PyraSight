import { useEffect, useState } from 'react'
import { Bell, FileText, Plus, RefreshCw, AlertTriangle } from 'lucide-react'
import { api, type Alert, type AlertRule, type Report } from '../lib/api'

export default function ReportsAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [rules, setRules] = useState<AlertRule[]>([])
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [reportType, setReportType] = useState('fire_activity')
  const [reportTitle, setReportTitle] = useState('')
  const [ruleName, setRuleName] = useState('')
  const [ruleType, setRuleType] = useState('high_confidence_detection')
  const [ruleConfig, setRuleConfig] = useState('{"minimum_confidence":"high"}')

  async function loadData() {
    setLoading(true); setError('')
    const results = await Promise.allSettled([api.alerts(), api.alertRules(), api.reports()])
    if (results[0].status === 'fulfilled') setAlerts(results[0].value)
    if (results[1].status === 'fulfilled') setRules(results[1].value)
    if (results[2].status === 'fulfilled') setReports(results[2].value)
    if (results.every(x => x.status === 'rejected')) setError('Could not load alerts and reports. Check the backend connection.')
    setLoading(false)
  }
  useEffect(() => { void loadData() }, [])

  async function generateReport(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError('')
    try { await api.createReport({ report_type: reportType, title: reportTitle.trim() || undefined }); setReportTitle(''); await loadData() }
    catch (err) { setError(err instanceof Error ? err.message : 'Report generation failed.') }
    finally { setBusy(false) }
  }
  async function createRule(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const config = JSON.parse(ruleConfig) as Record<string, unknown>
      await api.createAlertRule({ name: ruleName.trim(), rule_type: ruleType, config, enabled: true })
      setRuleName(''); await loadData()
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create rule. Check the JSON configuration.') }
    finally { setBusy(false) }
  }

  return <div className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="mb-2 flex items-center gap-2 text-sm font-medium text-orange-400"><Bell size={16}/> OPERATIONAL NOTIFICATIONS</p><h1 className="text-2xl font-semibold text-white">Reports & Alerts</h1><p className="mt-1 text-sm text-slate-400">Review generated alerts, configure rules and request analytical reports.</p></div><button onClick={() => void loadData()} disabled={loading} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"><RefreshCw size={15} className={loading ? 'animate-spin' : ''}/> Refresh</button></div>
    {error && <div className="flex gap-2 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300"><AlertTriangle size={17}/>{error}</div>}
    <div className="grid gap-4 sm:grid-cols-3">{[['Alerts', alerts.length], ['Configured rules', rules.length], ['Reports', reports.length]].map(([label, value]) => <div key={String(label)} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><p className="text-sm text-slate-400">{label}</p><p className="mt-3 text-2xl font-semibold text-white">{loading ? '...' : value}</p></div>)}</div>
    <div className="grid gap-5 xl:grid-cols-2">
      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><h2 className="mb-4 font-semibold text-white">Create an alert rule</h2><form onSubmit={createRule} className="space-y-3"><input required value={ruleName} onChange={e => setRuleName(e.target.value)} placeholder="Rule name" className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"/><select value={ruleType} onChange={e => setRuleType(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"><option value="high_confidence_detection">High-confidence detection</option><option value="fire_danger">Fire danger</option><option value="detection_threshold">Detection threshold</option><option value="custom">Custom rule type</option></select><label className="block text-xs text-slate-400">Rule configuration (JSON)</label><textarea rows={4} value={ruleConfig} onChange={e => setRuleConfig(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-white"/><button disabled={busy} className="flex items-center gap-2 rounded-lg bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Plus size={16}/> Create rule</button></form><div className="mt-5 space-y-2">{rules.map(rule => <div key={rule.id} className="flex items-center justify-between rounded-lg border border-slate-800 p-3"><div><p className="text-sm text-white">{rule.name}</p><p className="text-xs text-slate-500">{rule.rule_type}</p></div><span className={`text-xs ${rule.enabled ? 'text-emerald-400' : 'text-slate-500'}`}>{rule.enabled ? 'Enabled' : 'Disabled'}</span></div>)}{!loading && rules.length === 0 && <p className="text-xs text-slate-500">No alert rules returned by the backend.</p>}</div></section>
      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><h2 className="mb-4 font-semibold text-white">Generate a report</h2><form onSubmit={generateReport} className="space-y-3"><input value={reportTitle} onChange={e => setReportTitle(e.target.value)} placeholder="Optional report title" className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"/><select value={reportType} onChange={e => setReportType(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"><option value="fire_activity">Fire activity</option><option value="detection_summary">Detection summary</option><option value="model_predictions">Model predictions</option><option value="incident_summary">Incident summary</option></select><button disabled={busy} className="flex items-center gap-2 rounded-lg bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><FileText size={16}/> Generate report</button></form><div className="mt-5 space-y-2">{reports.map(report => <div key={report.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 p-3"><div className="min-w-0"><p className="truncate text-sm text-white">{report.title}</p><p className="text-xs text-slate-500">{report.report_type} · {new Date(report.created_at).toLocaleString()}</p></div><div className="flex items-center gap-3"><span className="text-xs text-slate-400">{report.status}</span>{report.download_url && <a href={report.download_url} target="_blank" rel="noreferrer" className="text-xs text-orange-400">Download</a>}</div></div>)}{!loading && reports.length === 0 && <p className="text-xs text-slate-500">No reports returned by the backend.</p>}</div></section>
    </div>
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"><h2 className="mb-4 font-semibold text-white">Alert feed</h2>{alerts.length === 0 ? <p className="py-8 text-center text-sm text-slate-500">{loading ? 'Loading alerts...' : 'No alerts returned by the backend.'}</p> : <div className="space-y-2">{alerts.map(alert => <div key={alert.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 p-3"><div><p className="text-sm font-medium text-white">{alert.name}</p><p className="mt-1 text-xs text-slate-400">{alert.message}</p><p className="mt-1 text-xs text-slate-600">{new Date(alert.created_at).toLocaleString()}</p></div><div className="flex gap-2 text-xs"><span className="rounded border border-slate-700 px-2 py-1 text-slate-300">{alert.severity}</span><span className="rounded border border-slate-700 px-2 py-1 text-slate-400">{alert.acknowledged ? 'Acknowledged' : 'Unacknowledged'}</span></div></div>)}</div>}<p className="mt-4 text-xs text-slate-600">The current API client has no alert-acknowledgement or rule-update method, so those actions are not simulated.</p></section>
  </div>
}
