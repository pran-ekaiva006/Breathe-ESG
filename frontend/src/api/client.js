import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  headers: { 'Content-Type': 'application/json' },
})

// ── Emissions ─────────────────────────────────────────────────────────────────
export const getEmissions = (params = {}) =>
  api.get('/api/emissions/', { params }).then(r => r.data)

export const getEmission = (id) =>
  api.get(`/api/emissions/${id}/`).then(r => r.data)

export const getEmissionIssues = (id, params = {}) =>
  api.get(`/api/emissions/${id}/issues/`, { params }).then(r => r.data)

export const getEmissionAudits = (id, params = {}) =>
  api.get(`/api/emissions/${id}/audits/`, { params }).then(r => r.data)

// ── Validation Issues ────────────────────────────────────────────────────────
export const getValidationIssues = (params = {}) =>
  api.get('/api/validation-issues/', { params }).then(r => r.data)

// ── Audit Logs ────────────────────────────────────────────────────────────────
export const getAuditLogs = (params = {}) =>
  api.get('/api/audit-logs/', { params }).then(r => r.data)

// ── Ingestion Uploads ────────────────────────────────────────────────────────
export const uploadSAP = (formData) =>
  api.post('/api/uploads/sap/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)

export const uploadUtility = (formData) =>
  api.post('/api/uploads/utility/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)

export const uploadTravel = (formData) =>
  api.post('/api/uploads/travel/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)

export const normalizeSAP = (id) =>
  api.post(`/api/uploads/sap/${id}/normalize/`).then(r => r.data)

export const normalizeUtility = (id) =>
  api.post(`/api/uploads/utility/${id}/normalize/`).then(r => r.data)

export const normalizeTravel = (id) =>
  api.post(`/api/uploads/travel/${id}/normalize/`).then(r => r.data)

export default api
