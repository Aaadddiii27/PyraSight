
import { useEffect, useMemo, useState } from 'react'
import { Activity, Flame, RefreshCw, Satellite, History, AlertTriangle } from 'lucide-react'
import { api, type TrendPoint, type PredictionHistoryItem, type HistorySummary } from '../lib/api'

export default function FireHistory() {
  const [summary, setSummary] = useState<HistorySummary | null>(null)
  const [historyTrends, setHistoryTrends] = useState<TrendPoint[]>([])
  const [firmsTrends, setFirmsTrends] = useState<TrendPoint[]>([])
  const [algerianRecords, setAlgerianRecords] = useState<PredictionHistoryItem[]>([])
  const [mesogeosRecords, setMesogeosRecords] = useState<PredictionHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadHistory = async () => {
    setLoading(true)
    setError('')

    try {
      const results = await Promise.allSettled([
        api.historySummary(),
        api.historyTrends(),
        api.firmsTrends(),
        api.algerianHistory(),
        api.mesogeosHistory(),
      ])

      const [summaryResult, historyResult, firmsResult, algerianResult, mesogeosResult] = results

      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value)
      if (historyResult.status === 'fulfilled') setHistoryTrends(historyResult.value)
      if (firmsResult.status === 'fulfilled') setFirmsTrends(firmsResult.value)
      if (algerianResult.status === 'fulfilled') setAlgerianRecords(algerianResult.value)
      if (mesogeosResult.status === 'fulfilled') setMesogeosRecords(mesogeosResult.value)

      if (results.every((item) => item.status === 'rejected')) {
        throw new Error('Unable to load historical data. Check whether the backend is running.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load historical data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadHistory()
  }, [])

  const totalModelPredictions =
    (summary?.total_predictions ?? 0)

  const combinedRecords = useMemo(
    () => [
      ...algerianRecords.map((item) => ({ ...item, sourceLabel: 'Algerian Model' })),
      ...mesogeosRecords.map((item) => ({ ...item, sourceLabel: 'Mesogeos Model' })),
    ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()),
    [algerianRecords, mesogeosRecords]
  )

  const maxTrend = Math.max(
    1,
    ...historyTrends.map((item) => item.count),
    ...firmsTrends.map((item) => item.count)
  )

  const formatDate = (date: string) => {
    const parsed = new Date(date)
    return Number.isNaN(parsed.getTime())
      ? date
      : parsed.toLocaleDateString()
  }

  const stats = [
    {
      label: 'Total Predictions',
      value: summary?.total_predictions ?? '—',
      icon: Activity,
      color: 'text-blue-400',
    },
    {
      label: 'Algerian Predictions',
      value: summary?.algerian_predictions ?? '—',
      icon: Flame,
      color: 'text-orange-400',
    },
    {
      label: 'Mesogeos Predictions',
      value: summary?.mesogeos_predictions ?? '—',
      icon: Satellite,
      color: 'text-purple-400',
    },
    {
      label: 'FIRMS Detections',
      value: summary?.total_firms_detections?.toLocaleString() ?? '—',
      icon: History,
      color: 'text-emerald-400',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-orange-400 text-sm font-medium mb-2">
            <History size={16} />
            HISTORICAL INTELLIGENCE
          </div>
          <h1 className="text-2xl font-semibold text-white">Fire History</h1>
          <p className="text-sm text-slate-400 mt-1">
            Explore historical satellite detections and recorded model predictions.
          </p>
        </div>

        <button
          onClick={() => void loadHistory()}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex gap-2 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300">
          <AlertTriangle size={17} />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">{stat.label}</span>
                <Icon size={19} className={stat.color} />
              </div>
              <p className="mt-3 text-2xl font-semibold text-white">
                {loading ? '...' : stat.value}
              </p>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-semibold text-white">Prediction Activity</h2>
              <p className="text-xs text-slate-500 mt-1">Historical prediction records by date</p>
            </div>
            <Activity size={19} className="text-blue-400" />
          </div>

          {historyTrends.length === 0 ? (
            <p className="py-12 text-center text-sm text-slate-500">
              {loading ? 'Loading prediction trends...' : 'No prediction trend data available.'}
            </p>
          ) : (
            <div className="space-y-4">
              {historyTrends.slice(-10).map((point, index) => (
                <div key={`${point.date}-${index}`}>
                  <div className="flex justify-between text-xs mb-2">
                    <span className="text-slate-400">{formatDate(point.date)}</span>
                    <span className="text-white">{point.count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{ width: `${(point.count / maxTrend) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-semibold text-white">Satellite Detection Activity</h2>
              <p className="text-xs text-slate-500 mt-1">Historical FIRMS detection counts</p>
            </div>
            <Satellite size={19} className="text-emerald-400" />
          </div>

          {firmsTrends.length === 0 ? (
            <p className="py-12 text-center text-sm text-slate-500">
              {loading ? 'Loading satellite trends...' : 'No satellite trend data available.'}
            </p>
          ) : (
            <div className="space-y-4">
              {firmsTrends.slice(-10).map((point, index) => (
                <div key={`${point.date}-${index}`}>
                  <div className="flex justify-between text-xs mb-2">
                    <span className="text-slate-400">{formatDate(point.date)}</span>
                    <span className="text-white">{point.count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-500"
                      style={{ width: `${(point.count / maxTrend) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <h2 className="font-semibold text-white">Prediction History</h2>
            <p className="text-xs text-slate-500 mt-1">
              Previously recorded predictions from both models
            </p>
          </div>
          <span className="text-xs text-slate-400">
            {combinedRecords.length} records loaded
          </span>
        </div>

        {combinedRecords.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-500">
            {loading ? 'Loading prediction records...' : 'No saved prediction records found.'}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs text-slate-500">
                  <th className="py-3 pr-4 font-medium">Model</th>
                  <th className="py-3 pr-4 font-medium">Prediction</th>
                  <th className="py-3 pr-4 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {combinedRecords.slice(0, 15).map((record) => (
                  <tr key={`${record.model}-${record.id}`} className="border-b border-slate-800/60">
                    <td className="py-3 pr-4 text-slate-300">{record.sourceLabel}</td>
                    <td className="py-3 pr-4 text-slate-300">
                      {String(record.response.label ?? record.response.prediction ?? 'Recorded')}
                    </td>
                    <td className="py-3 pr-4 text-slate-400">
                      {new Date(record.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-xs text-slate-500">
        Prediction records and satellite detections are different data types. Satellite
        detections indicate thermal anomalies and should not automatically be treated as
        confirmed fire incidents.
      </p>

      <p className="text-xs text-slate-600">
        {totalModelPredictions.toLocaleString()} total model predictions reported by the backend summary.
      </p>
    </div>
  )
}
