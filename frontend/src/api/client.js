const BASE = import.meta.env.VITE_API_BASE || '/api'

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  getBuildings: () => req('/buildings'),
  getBuildingDetail: (id, sessionId) =>
    req(`/buildings/${id}${sessionId ? `?session_id=${sessionId}` : ''}`),
  getBoundary: () => req('/geo/boundary'),

  listSessions: () => req('/sessions'),
  createSession: (name) =>
    req('/sessions', { method: 'POST', body: JSON.stringify({ name }) }),
  deleteSession: (id) => req(`/sessions/${id}`, { method: 'DELETE' }),

  randomize: (id) => req(`/sessions/${id}/randomize`, { method: 'POST' }),
  tick: (id) => req(`/sessions/${id}/tick`, { method: 'POST' }),
  pause: (id) => req(`/sessions/${id}/pause`, { method: 'POST' }),

  listYears: (id) => req(`/sessions/${id}/snapshots`),
  getSnapshot: (id, year) => req(`/sessions/${id}/snapshots/${year}`),
  getMovements: (id, year, limit = 50) =>
    req(`/sessions/${id}/movements?year=${year}&limit=${limit}`),
}
