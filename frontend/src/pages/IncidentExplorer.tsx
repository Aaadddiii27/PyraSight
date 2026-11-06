
import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Bookmark,
  MapPin,
  Plus,
  Pencil,
  Trash2,
  RefreshCw,
  Search,
  ShieldAlert,
  X,
} from 'lucide-react'
import { api, type Incident } from '../lib/api'

export default function IncidentExplorer() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [selected, setSelected] = useState<Incident | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [saving, setSaving] = useState(false)

  const [editForm, setEditForm] = useState({
    title: '',
    latitude: '',
    longitude: '',
    description: '',
    severity: 'medium',
  })
  const [note, setNote] = useState('')

  const [form, setForm] = useState({
    title: '',
    latitude: '',
    longitude: '',
    description: '',
    severity: 'medium',
    source: 'analyst',
  })

  const loadIncidents = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.incidents()
      setIncidents(data)
      setSelected((current) =>
        current ? data.find((item) => item.id === current.id) ?? null : null
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load incidents.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadIncidents()
  }, [])

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      const matchesSearch =
        incident.title.toLowerCase().includes(search.toLowerCase()) ||
        incident.description?.toLowerCase().includes(search.toLowerCase()) ||
        incident.source.toLowerCase().includes(search.toLowerCase())

      const matchesStatus =
        statusFilter === 'All' ||
        incident.status.toLowerCase() === statusFilter.toLowerCase()

      return matchesSearch && matchesStatus
    })
  }, [incidents, search, statusFilter])

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    const latitude = Number(form.latitude)
    const longitude = Number(form.longitude)

    if (!form.title.trim() || !form.latitude || !form.longitude) {
      setError('Title, latitude and longitude are required.')
      return
    }

    if (
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude) ||
      latitude < -90 || latitude > 90 ||
      longitude < -180 || longitude > 180
    ) {
      setError('Enter valid geographic coordinates.')
      return
    }

    setSaving(true)
    try {
      await api.createIncident({
        title: form.title.trim(),
        latitude,
        longitude,
        description: form.description.trim(),
        severity: form.severity,
        source: form.source,
      })

      setForm({
        title: '',
        latitude: '',
        longitude: '',
        description: '',
        severity: 'medium',
        source: 'analyst',
      })
      setShowCreate(false)
      await loadIncidents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create incident.')
    } finally {
      setSaving(false)
    }
  }

  const openEdit = (incident: Incident) => {
    setEditForm({
      title: incident.title,
      latitude: String(incident.latitude),
      longitude: String(incident.longitude),
      description: incident.description ?? '',
      severity: incident.severity,
    })
    setError('')
    setShowEdit(true)
  }

  const handleEdit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selected) return

    const latitude = Number(editForm.latitude)
    const longitude = Number(editForm.longitude)

    if (
      !editForm.title.trim() ||
      editForm.latitude.trim() === '' ||
      editForm.longitude.trim() === '' ||
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude) ||
      latitude < -90 || latitude > 90 ||
      longitude < -180 || longitude > 180
    ) {
      setError('Enter a valid title and geographic coordinates.')
      return
    }

    setSaving(true)
    setError('')
    try {
      await api.updateIncident(selected.id, {
        title: editForm.title.trim(),
        latitude,
        longitude,
        description: editForm.description.trim(),
        severity: editForm.severity,
      })
      setShowEdit(false)
      await loadIncidents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not edit incident.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selected || deleting) return

    const confirmed = window.confirm(
      `Delete "${selected.title}"? This action cannot be undone.`
    )
    if (!confirmed) return

    setDeleting(true)
    setError('')
    try {
      await api.deleteIncident(selected.id)
      setSelected(null)
      await loadIncidents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete incident.')
    } finally {
      setDeleting(false)
    }
  }

  const handleBookmark = async (incident: Incident) => {
    setError('')
    try {
      await api.updateIncident(incident.id, {
        bookmarked: !incident.bookmarked,
      })
      await loadIncidents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update bookmark.')
    }
  }

  const handleStatusChange = async (incident: Incident, status: string) => {
    setError('')
    try {
      await api.updateIncident(incident.id, { status })
      await loadIncidents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update incident status.')
    }
  }

  const handleAddNote = async () => {
    if (!selected || !note.trim()) return

    setSaving(true)
    setError('')
    try {
      await api.addNote(selected.id, note.trim())
      setNote('')
      await loadIncidents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add note.')
    } finally {
      setSaving(false)
    }
  }

  const severityClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'text-red-400 bg-red-950/40 border-red-900/50'
      case 'medium':
        return 'text-orange-400 bg-orange-950/40 border-orange-900/50'
      default:
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-900/50'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-orange-400 text-sm font-medium mb-2">
            <ShieldAlert size={16} />
            INCIDENT INVESTIGATION
          </div>
          <h1 className="text-2xl font-semibold text-white">Incident Explorer</h1>
          <p className="text-sm text-slate-400 mt-1">
            Review incident records, track investigation status and maintain analyst notes.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => void loadIncidents()}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-800"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 rounded-lg bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-600"
          >
            <Plus size={16} />
            New Incident
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300">
          <AlertTriangle size={17} />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError('')}><X size={16} /></button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Total Incidents', value: incidents.length },
          { label: 'Open Incidents', value: incidents.filter((i) => i.status.toLowerCase() === 'open').length },
          { label: 'Bookmarked', value: incidents.filter((i) => i.bookmarked).length },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <p className="text-sm text-slate-400">{item.label}</p>
            <p className="mt-3 text-2xl font-semibold text-white">
              {loading ? '...' : item.value}
            </p>
          </div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={17} className="absolute left-3 top-3 text-slate-500" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search incidents..."
            className="w-full rounded-lg border border-slate-800 bg-slate-900 py-3 pl-10 pr-3 text-sm text-white outline-none focus:border-orange-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none"
        >
          <option>All</option>
          <option>Open</option>
          <option>Investigating</option>
          <option>Resolved</option>
        </select>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_0.9fr] gap-5">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="font-semibold text-white mb-4">Incident Records</h2>

          {loading ? (
            <p className="py-10 text-center text-sm text-slate-500">Loading incidents...</p>
          ) : filteredIncidents.length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-500">No matching incidents found.</p>
          ) : (
            <div className="space-y-2">
              {filteredIncidents.map((incident) => (
                <button
                  key={incident.id}
                  onClick={() => setSelected(incident)}
                  className={`w-full rounded-lg border p-4 text-left transition ${
                    selected?.id === incident.id
                      ? 'border-orange-500/60 bg-orange-950/20'
                      : 'border-slate-800 bg-slate-950/40 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium text-white truncate">{incident.title}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {incident.source} · {new Date(incident.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className={`shrink-0 rounded-md border px-2 py-1 text-xs ${severityClass(incident.severity)}`}>
                      {incident.severity}
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                    <span>{incident.status}</span>
                    <span className="flex items-center gap-1">
                      <MapPin size={13} />
                      {incident.latitude.toFixed(3)}, {incident.longitude.toFixed(3)}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          {!selected ? (
            <div className="flex min-h-[350px] flex-col items-center justify-center text-center">
              <ShieldAlert size={32} className="text-slate-600 mb-3" />
              <p className="text-sm text-slate-300">Select an incident</p>
              <p className="text-xs text-slate-500 mt-1">Investigation details will appear here.</p>
            </div>
          ) : (
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs text-orange-400 font-medium">INCIDENT DETAILS</p>
                  <h2 className="text-lg font-semibold text-white mt-1">{selected.title}</h2>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEdit(selected)}
                    className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:bg-slate-800"
                    title="Edit incident"
                    aria-label="Edit incident"
                  >
                    <Pencil size={17} />
                  </button>
                  <button
                    onClick={() => void handleDelete()}
                    disabled={deleting}
                    className="rounded-lg border border-red-900/60 p-2 text-red-400 hover:bg-red-950/40 disabled:opacity-50"
                    title="Delete incident"
                    aria-label="Delete incident"
                  >
                    <Trash2 size={17} />
                  </button>
                  <button
                    onClick={() => void handleBookmark(selected)}
                    className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:bg-slate-800"
                    title="Toggle bookmark"
                    aria-label="Toggle bookmark"
                  >
                    <Bookmark size={17} className={selected.bookmarked ? 'fill-orange-400 text-orange-400' : ''} />
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <span className={`rounded-md border px-2 py-1 text-xs ${severityClass(selected.severity)}`}>
                  {selected.severity} severity
                </span>
                <span className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
                  Source: {selected.source}
                </span>
              </div>

              <p className="text-sm leading-relaxed text-slate-400">
                {selected.description || 'No description provided.'}
              </p>

              <div className="rounded-lg bg-slate-950 p-3">
                <p className="text-xs text-slate-500 mb-2">LOCATION COORDINATES</p>
                <p className="text-sm text-white">
                  {selected.latitude}, {selected.longitude}
                </p>
              </div>

              <div>
                <label className="text-xs text-slate-500">INVESTIGATION STATUS</label>
                <select
                  value={selected.status}
                  onChange={(event) => void handleStatusChange(selected, event.target.value)}
                  className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white"
                >
                  <option value="open">Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>

              <div>
                <h3 className="text-sm font-medium text-white mb-3">Analyst Notes</h3>
                <div className="space-y-2 mb-3">
                  {selected.notes.length === 0 ? (
                    <p className="text-xs text-slate-500">No notes added yet.</p>
                  ) : selected.notes.map((item, index) => (
                    <div key={`${item.timestamp}-${index}`} className="rounded-lg bg-slate-950 p-3">
                      <p className="text-sm text-slate-300">{item.content}</p>
                      <p className="text-xs text-slate-600 mt-2">
                        {new Date(item.timestamp).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
                <textarea
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder="Add an investigation note..."
                  rows={3}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white outline-none focus:border-orange-500"
                />
                <button
                  onClick={() => void handleAddNote()}
                  disabled={saving || !note.trim()}
                  className="mt-2 rounded-lg bg-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-600 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Add Note'}
                </button>
              </div>
            </div>
          )}
        </section>
      </div>

      {showEdit && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <form
            onSubmit={handleEdit}
            className="w-full max-w-lg space-y-4 rounded-xl border border-slate-700 bg-slate-900 p-6"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Edit Incident</h2>
              <button
                type="button"
                onClick={() => setShowEdit(false)}
                className="text-slate-400 hover:text-white"
                aria-label="Close edit form"
              >
                <X size={20} />
              </button>
            </div>

            <input
              required
              maxLength={200}
              value={editForm.title}
              onChange={(event) => setEditForm({ ...editForm, title: event.target.value })}
              placeholder="Incident title"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
            />

            <div className="grid grid-cols-2 gap-3">
              <input
                required
                type="number"
                min="-90"
                max="90"
                step="any"
                value={editForm.latitude}
                onChange={(event) => setEditForm({ ...editForm, latitude: event.target.value })}
                placeholder="Latitude"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
              />
              <input
                required
                type="number"
                min="-180"
                max="180"
                step="any"
                value={editForm.longitude}
                onChange={(event) => setEditForm({ ...editForm, longitude: event.target.value })}
                placeholder="Longitude"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
              />
            </div>

            <textarea
              value={editForm.description}
              onChange={(event) => setEditForm({ ...editForm, description: event.target.value })}
              placeholder="Description"
              rows={3}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
            />

            <select
              value={editForm.severity}
              onChange={(event) => setEditForm({ ...editForm, severity: event.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowEdit(false)}
                className="rounded-lg border border-slate-700 px-4 py-3 text-sm text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-orange-500 px-5 py-3 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <form
            onSubmit={handleCreate}
            className="w-full max-w-lg space-y-4 rounded-xl border border-slate-700 bg-slate-900 p-6"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Create Incident</h2>
              <button type="button" onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            <input
              required
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              placeholder="Incident title"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
            />

            <div className="grid grid-cols-2 gap-3">
              <input
                required
                type="number"
                step="any"
                value={form.latitude}
                onChange={(event) => setForm({ ...form, latitude: event.target.value })}
                placeholder="Latitude"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
              />
              <input
                required
                type="number"
                step="any"
                value={form.longitude}
                onChange={(event) => setForm({ ...form, longitude: event.target.value })}
                placeholder="Longitude"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
              />
            </div>

            <textarea
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="Description"
              rows={3}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
            />

            <div className="grid grid-cols-2 gap-3">
              <select
                value={form.severity}
                onChange={(event) => setForm({ ...form, severity: event.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
              <select
                value={form.source}
                onChange={(event) => setForm({ ...form, source: event.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-white"
              >
                <option value="analyst">Analyst</option>
                <option value="firms">FIRMS</option>
                <option value="official">Official</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-lg bg-orange-500 py-3 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create Incident'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
