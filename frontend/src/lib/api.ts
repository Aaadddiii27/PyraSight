const API_BASE = '/api/v1'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || `API error ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Health
  health: () => request<{ status: string; version: string; models: Record<string, string>; data_mode: string }>('/health'),

  // Predictions
  predictAlgerian: (data: Record<string, number>) =>
    request<AlgerianPrediction>('/predictions/algerian', { method: 'POST', body: JSON.stringify(data) }),
  predictMesogeos: (data: Record<string, number>) =>
    request<MesogeosPrediction>('/predictions/mesogeos', { method: 'POST', body: JSON.stringify(data) }),
  algerianHistory: () => request<PredictionHistoryItem[]>('/predictions/algerian/history'),
  mesogeosHistory: () => request<PredictionHistoryItem[]>('/predictions/mesogeos/history'),

  // FIRMS
  firmsDetections: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<FIRMSResponse>(`/firms/detections${qs}`)
  },
  firmsStatus: () => request<FIRMSStatusResponse>('/firms/status'),
  firmsSummary: () => request<FIRMSSummaryResponse>('/firms/summary'),
  firmsTrends: () => request<TrendPoint[]>('/firms/trends'),

  // Models
  models: () => request<ModelInfo[]>('/models'),
  modelMetrics: (id: string) => request<Record<string, unknown>>(`/models/${id}/metrics`),
  modelExplanations: (id: string) => request<{ model_id: string; method: string; feature_importance: Record<string, number> }>(`/models/${id}/explanations`),

  // Incidents
  incidents: () => request<Incident[]>('/incidents'),
  createIncident: (data: { title: string; latitude: number; longitude: number; description?: string; source?: string; severity?: string }) =>
    request<Incident>('/incidents', { method: 'POST', body: JSON.stringify(data) }),
  updateIncident: (id: string, data: Record<string, unknown>) =>
    request<Incident>(`/incidents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteIncident: (id: string) =>
  request<{ message: string; id: string }>(`/incidents/${id}`, {
    method: 'DELETE',
  }),
  addNote: (id: string, content: string) =>
    request<Incident>(`/incidents/${id}/notes`, { method: 'POST', body: JSON.stringify({ content }) }),

  // Alerts
  alerts: () => request<Alert[]>('/alerts'),
  alertRules: () => request<AlertRule[]>('/alerts/rules'),
  createAlertRule: (data: { name: string; rule_type: string; config: Record<string, unknown>; enabled?: boolean }) =>
    request<AlertRule>('/alerts/rules', { method: 'POST', body: JSON.stringify(data) }),

  // Reports
  reports: () => request<Report[]>('/reports'),
  createReport: (data: { report_type: string; title?: string }) =>
    request<Report>('/reports', { method: 'POST', body: JSON.stringify(data) }),

  // History
  historySummary: () => request<HistorySummary>('/history/summary'),
  historyTrends: () => request<TrendPoint[]>('/history/trends'),
}

// Types
export interface AlgerianPrediction {
  prediction: number; label: string; probability_fire: number; probability_no_fire: number
  risk_level: string; threshold: number; model_type: string
  feature_contributions: { feature: string; value: number; importance: number; direction: string }[]
  disclaimer: string
}

export interface MesogeosPrediction {
  prediction: number; label: string; probability_danger: number; probability_safe: number
  danger_level: string; model_type: string
  feature_contributions: { feature: string; value: number; importance: number }[]
  disclaimer: string
}

export interface PredictionHistoryItem {
  id: string; model: string; request: Record<string, number>; response: Record<string, unknown>; timestamp: string
}

export interface FIRMSDetection {
  latitude: number; longitude: number; bright_ti4: number | null; bright_ti5: number | null
  scan: number | null; track: number | null; acq_date: string; acq_time: string
  satellite: string; confidence: string; version: string; frp: number | null; daynight: string; product: string
}

export interface FIRMSResponse {
  detections: FIRMSDetection[]; total: number; returned: number
  source: string; date_range: { min: string; max: string }; data_mode: string
}

export interface FIRMSStatusResponse {
  data_mode: string; last_loaded: string | null; files_available: Record<string, boolean>; total_detections: number
}

export interface FIRMSSummaryResponse {
  total_detections: number; by_satellite: Record<string, number>
  by_confidence: Record<string, number>; by_daynight: Record<string, number>
  date_range: { min: string; max: string }; data_mode: string
}

export interface TrendPoint { date: string; count: number; satellite?: string }

export interface ModelInfo {
  model_id: string; model_type?: string; dataset?: string; n_train?: number; n_test?: number
  features?: string[]; target?: string; geographic_scope?: string; status: string
  evaluation?: Record<string, unknown>
}

export interface Incident {
  id: string; title: string; latitude: number; longitude: number; description?: string
  source: string; severity: string; status: string; created_at: string; updated_at: string
  notes: { content: string; timestamp: string }[]; bookmarked: boolean
}

export interface Alert {
  id: string; name: string; rule_type: string; message: string; severity: string
  created_at: string; acknowledged: boolean
}

export interface AlertRule {
  id: string; name: string; rule_type: string; config: Record<string, unknown>; enabled: boolean; created_at: string
}

export interface Report {
  id: string; title: string; report_type: string; created_at: string; status: string; download_url?: string
}

export interface HistorySummary {
  total_predictions: number; algerian_predictions: number; mesogeos_predictions: number
  total_incidents: number; total_firms_detections: number
}
