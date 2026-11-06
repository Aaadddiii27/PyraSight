
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Flame,
  Radio,
  Satellite,
  RefreshCw,
  AlertTriangle,
  Database,
  ArrowUpRight,
  Clock3,
} from 'lucide-react'

import { api } from '../lib/api'
import StatCard from '../components/StatCard'

function formatNumber(value?: number) {
  return value === undefined ? '—' : value.toLocaleString()
}

function CommandCenter() {
  const summary = useQuery({
    queryKey: ['firms-summary'],
    queryFn: api.firmsSummary,
    retry: 1,
  })

  const status = useQuery({
    queryKey: ['firms-status'],
    queryFn: api.firmsStatus,
    retry: 1,
  })

  const history = useQuery({
    queryKey: ['history-summary'],
    queryFn: api.historySummary,
    retry: 1,
  })

  const trends = useQuery({
    queryKey: ['firms-trends'],
    queryFn: api.firmsTrends,
    retry: 1,
  })

  const models = useQuery({
    queryKey: ['models'],
    queryFn: api.models,
    retry: 1,
  })

  const isRefreshing =
    summary.isFetching ||
    status.isFetching ||
    history.isFetching

  const refreshAll = () => {
    void summary.refetch()
    void status.refetch()
    void history.refetch()
    void trends.refetch()
    void models.refetch()
  }

  const total = summary.data?.total_detections
  const satellites = summary.data?.by_satellite ?? {}
  const confidence = summary.data?.by_confidence ?? {}
  const trendData = trends.data ?? []

  const dailyTotals = trendData.reduce<Record<string, number>>(
  (acc, item) => {
    acc[item.date] = (acc[item.date] ?? 0) + item.count
    return acc
  },
  {}
)

  const latestTrend = Object.entries(dailyTotals)
  .sort(([dateA], [dateB]) => dateA.localeCompare(dateB))
  .slice(-7)
  .map(([date, count]) => ({ date, count }))

  const maxTrend = Math.max(1, ...latestTrend.map(item => item.count))

  const sourceAvailable =
    status.data &&
    Object.values(status.data.files_available).some(Boolean)

  const backendError =
    summary.isError &&
    status.isError &&
    history.isError

  return (
    <div className="space-y-7">

      {/* Dashboard heading */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium uppercase tracking-wider text-pyra-muted">
              Intelligence overview
            </span>
          </div>

          <p className="text-sm text-pyra-muted">
            A unified view of satellite observations and wildfire intelligence.
          </p>
        </div>

        <button
          onClick={refreshAll}
          disabled={isRefreshing}
          className="inline-flex items-center gap-2 rounded-lg border border-pyra-border bg-pyra-surface px-4 py-2.5 text-xs font-medium text-white transition hover:bg-pyra-hover disabled:opacity-50"
        >
          <RefreshCw
            size={14}
            className={isRefreshing ? 'animate-spin' : ''}
          />
          Refresh data
        </button>
      </div>

      {/* Backend warning */}
      {backendError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <AlertTriangle className="mt-0.5 text-red-400" size={19} />
          <div>
            <p className="text-sm font-medium text-red-300">
              Dashboard data unavailable
            </p>
            <p className="mt-1 text-xs text-pyra-muted">
              Could not retrieve data from the backend. Check that FastAPI
              is running and the frontend API proxy is configured.
            </p>
          </div>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <StatCard
          title="Satellite Detections"
          value={summary.isLoading ? '...' : formatNumber(total)}
          description="Records in available FIRMS data"
          icon={Satellite}
          accent="orange"
        />

        <StatCard
          title="Fire Danger Predictions"
          value={
            history.isLoading
              ? '...'
              : formatNumber(history.data?.total_predictions)
          }
          description="Recorded model predictions"
          icon={Flame}
          accent="green"
        />

        <StatCard
          title="Active Models"
          value={
            models.isLoading
              ? '...'
              : formatNumber(
                  models.data?.filter(model => model.status === 'ready').length
                )
          }
          description="Models reported as available"
          icon={Activity}
          accent="blue"
        />

        <StatCard
          title="Recorded Incidents"
          value={
            history.isLoading
              ? '...'
              : formatNumber(history.data?.total_incidents)
          }
          description="Saved incident records"
          icon={Radio}
          accent="purple"
        />

      </div>

      {/* Main analytics */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">

        {/* Detection trend */}
        <div className="rounded-xl border border-pyra-border bg-pyra-surface p-5 xl:col-span-2">

          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">
                Detection Activity
              </h2>
              <p className="mt-1 text-xs text-pyra-muted">
                Daily satellite detection records
              </p>
            </div>

            <span className="rounded-md border border-pyra-border px-2.5 py-1 text-[10px] text-pyra-muted">
              Latest available records
            </span>
          </div>

          {trends.isLoading ? (
            <div className="flex h-48 items-center justify-center text-xs text-pyra-muted">
              Loading detection trends...
            </div>
          ) : trends.isError ? (
            <div className="flex h-48 items-center justify-center text-xs text-pyra-muted">
              Detection trend data unavailable.
            </div>
          ) : latestTrend.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
              <Activity size={24} className="text-pyra-muted" />
              <p className="text-sm text-pyra-muted">
                No detection trend data available.
              </p>
            </div>
          ) : (
            <div className="flex h-48 items-end gap-3 border-b border-pyra-border pb-2">
              {latestTrend.map((item, index) => (
                <div
                  key={item.date}
                  className="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2"
                >
                  <span className="text-[10px] text-pyra-muted">
                    {item.count.toLocaleString()}
                  </span>

                  <div
                    className="w-full max-w-12 rounded-t-md bg-orange-500/80 transition-all hover:bg-orange-400"
                    style={{
                      height: `${Math.max(3, (item.count / maxTrend) * 100)}%`,
                    }}
                    title={`${item.date}: ${item.count} detections`}
                  />

                  <span className="truncate text-[9px] text-pyra-muted">
                    {item.date.slice(5)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Satellite distribution */}
        <div className="rounded-xl border border-pyra-border bg-pyra-surface p-5">

          <div className="mb-6">
            <h2 className="text-sm font-semibold text-white">
              Satellite Distribution
            </h2>
            <p className="mt-1 text-xs text-pyra-muted">
              Detection records by satellite
            </p>
          </div>

          {summary.isLoading ? (
            <p className="py-10 text-center text-xs text-pyra-muted">
              Loading satellite data...
            </p>
          ) : Object.keys(satellites).length === 0 ? (
            <p className="py-10 text-center text-xs text-pyra-muted">
              No satellite distribution available.
            </p>
          ) : (
            <div className="space-y-5">
              {Object.entries(satellites).map(([name, count]) => {
                const percentage =
                  total && total > 0
                    ? (count / total) * 100
                    : 0

                return (
                  <div key={name}>
                    <div className="mb-2 flex justify-between gap-2">
                      <span className="text-xs text-pyra-muted">
                        {name}
                      </span>
                      <span className="text-xs font-medium text-white">
                        {count.toLocaleString()}
                      </span>
                    </div>

                    <div className="h-1.5 overflow-hidden rounded-full bg-pyra-hover">
                      <div
                        className="h-full rounded-full bg-orange-400"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          <div className="mt-7 border-t border-pyra-border pt-4">
            <p className="mb-3 text-[10px] uppercase tracking-wider text-pyra-muted">
              Detection confidence
            </p>

            <div className="space-y-2">
              {Object.entries(confidence).map(([name, count]) => (
                <div key={name} className="flex justify-between text-xs">
                  <span className="text-pyra-muted">{name}</span>
                  <span className="text-white">
                    {count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* System status */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">

        <div className="rounded-xl border border-pyra-border bg-pyra-surface p-5">
          <div className="mb-5 flex items-center gap-2">
            <Database size={17} className="text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">
              Data Source Health
            </h2>
          </div>

          {status.isLoading ? (
            <p className="text-xs text-pyra-muted">Checking data sources...</p>
          ) : status.isError ? (
            <p className="text-xs text-red-300">Data-source status unavailable.</p>
          ) : (
            <>
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs text-pyra-muted">
                  FIRMS data mode
                </span>
                <span className="rounded-md bg-orange-500/10 px-2 py-1 text-xs text-orange-300">
                  {status.data?.data_mode ?? 'Unknown'}
                </span>
              </div>

              <div className="space-y-3">
                {Object.entries(status.data?.files_available ?? {}).map(
                  ([name, available]) => (
                    <div key={name} className="flex items-center justify-between gap-3">
                      <span className="truncate text-xs text-pyra-muted">
                        {name}
                      </span>
                      <span className={`text-xs ${available ? 'text-emerald-400' : 'text-red-400'}`}>
                        {available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                  )
                )}
              </div>

              <div className="mt-5 flex items-center gap-2 border-t border-pyra-border pt-4 text-[10px] text-pyra-muted">
                <Clock3 size={13} />
                Last loaded: {status.data?.last_loaded ?? 'Not reported'}
              </div>
            </>
          )}
        </div>

        <div className="rounded-xl border border-pyra-border bg-pyra-surface p-5">
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity size={17} className="text-blue-400" />
              <h2 className="text-sm font-semibold text-white">
                Model Availability
              </h2>
            </div>

            <span className="text-xs text-pyra-muted">
              {models.data?.length ?? 0} registered
            </span>
          </div>

          {models.isLoading ? (
            <p className="text-xs text-pyra-muted">Loading models...</p>
          ) : models.isError ? (
            <p className="text-xs text-red-300">Model information unavailable.</p>
          ) : models.data?.length ? (
            <div className="space-y-4">
              {models.data.map(model => (
                <div
                  key={model.model_id}
                  className="flex items-center justify-between gap-3 border-b border-pyra-border pb-3 last:border-0"
                >
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-white">
                      {model.model_id}
                    </p>
                    <p className="mt-1 text-[10px] text-pyra-muted">
                      {model.dataset ?? 'Dataset not reported'}
                    </p>
                  </div>

                  <span className={`shrink-0 rounded-md px-2 py-1 text-[10px] ${
                    model.status === 'available'
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'bg-red-500/10 text-red-400'
                  }`}>
                    {model.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-pyra-muted">
              No model information reported by the backend.
            </p>
          )}

          <div className="mt-4 flex items-center gap-2 text-[10px] text-pyra-muted">
            <ArrowUpRight size={13} />
            Model status from backend
          </div>
        </div>
      </div>

      {/* Data disclaimer */}
      <div className="rounded-lg border border-pyra-border bg-pyra-card px-4 py-3">
        <p className="text-[10px] leading-relaxed text-pyra-muted">
          Satellite thermal detections are observations, not necessarily
          confirmed wildfires. Dashboard figures represent records reported
          by the configured data sources.
        </p>
      </div>
    </div>
  )
}

export default CommandCenter
