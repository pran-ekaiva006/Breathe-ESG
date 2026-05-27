import React, { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import api, { getEmission, getEmissionIssues, getEmissionAudits } from '../api/client'

const STATUS_STYLES = {
  pending:  { background: '#fefce8', color: '#a16207' },
  approved: { background: '#f0fdf4', color: '#15803d' },
  rejected: { background: '#fef2f2', color: '#dc2626' },
}

const SOURCE_STYLES = {
  SAP:     { background: '#f3f4f6', color: '#374151' },
  UTILITY: { background: '#eff6ff', color: '#1d4ed8' },
  TRAVEL:  { background: '#faf5ff', color: '#7c3aed' },
}

const SEVERITY_STYLES = {
  high:   { background: '#fef2f2', color: '#dc2626' },
  medium: { background: '#fffbeb', color: '#b45309' },
  low:    { background: '#f8fafc', color: '#475569' },
}

function Badge({ value, styles }) {
  const s = styles[value] || { background: '#f3f4f6', color: '#4b5563' }
  return (
    <span className="badge" style={s}>{value}</span>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <p style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>{label}</p>
      <p style={{ fontSize: '0.875rem', color: '#111827', margin: 0, wordBreak: 'break-word' }}>{children ?? '—'}</p>
    </div>
  )
}

export default function RecordDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [record, setRecord]   = useState(null)
  const [issues, setIssues]   = useState([])
  const [audits, setAudits]   = useState([])
  const [tab, setTab]         = useState('issues')
  const [loading, setLoading] = useState(true)
  
  // Action state
  const [actionLoading, setActionLoading] = useState(false)
  const [message, setMessage] = useState(null)

  const loadData = useCallback(() => {
    return Promise.all([
      getEmission(id),
      getEmissionIssues(id),
      getEmissionAudits(id),
    ]).then(([rec, iss, aud]) => {
      setRecord(rec)
      setIssues(iss.results || iss || [])
      setAudits(aud.results || aud || [])
    })
  }, [id])

  useEffect(() => {
    loadData().finally(() => setLoading(false))
  }, [loadData])

  const handleAction = async (actionType) => {
    setActionLoading(true)
    setMessage(null)
    try {
      await api.post(`/api/emissions/${id}/${actionType}/`)
      await loadData()
      setMessage({ type: 'success', text: `Record successfully ${actionType}d.` })
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err.response?.data?.error || `Failed to ${actionType} record.` 
      })
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <Layout title="Record Detail"><p style={{ fontSize: '0.85rem', color: '#6b7280' }}>Loading…</p></Layout>
  if (!record) return <Layout title="Record Detail"><p style={{ fontSize: '0.85rem', color: '#dc2626' }}>Record not found.</p></Layout>

  return (
    <Layout title={`Record #${record.id}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <button onClick={() => navigate(-1)} className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
          ← Back to Reviews
        </button>
        
        {/* Actions */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {actionLoading && <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Processing…</span>}
          <button 
            onClick={() => handleAction('approve')}
            disabled={record.locked || actionLoading || record.approval_status === 'approved'}
            className="btn"
            style={{ 
              background: '#15803d', color: '#fff', border: 'none', 
              opacity: (record.locked || actionLoading || record.approval_status === 'approved') ? 0.5 : 1 
            }}
          >
            Approve
          </button>
          <button 
            onClick={() => handleAction('reject')}
            disabled={record.locked || actionLoading || record.approval_status === 'rejected'}
            className="btn"
            style={{ 
              background: '#dc2626', color: '#fff', border: 'none',
              opacity: (record.locked || actionLoading || record.approval_status === 'rejected') ? 0.5 : 1
            }}
          >
            Reject
          </button>
        </div>
      </div>

      {/* Messaging */}
      {message && (
        <div style={{ 
          marginBottom: 20, padding: '12px 16px', borderRadius: 6, fontSize: '0.85rem',
          background: message.type === 'success' ? '#f0fdf4' : '#fef2f2',
          color: message.type === 'success' ? '#15803d' : '#dc2626',
          border: `1px solid ${message.type === 'success' ? '#bbf7d0' : '#fecaca'}`
        }}>
          {message.text}
        </div>
      )}

      {/* 1. Normalized Record Data */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #f3f4f6' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Badge value={record.source_type} styles={SOURCE_STYLES} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {record.scope_category}
            </span>
          </div>
          <Badge value={record.approval_status} styles={STATUS_STYLES} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20 }}>
          <Field label="Organization">{record.organization_name}</Field>
          <Field label="Activity Type">{record.activity_type}</Field>
          <Field label="Record Date">{record.record_date}</Field>
          <Field label="CO2e Emissions">{Number(record.co2e_value).toLocaleString(undefined, { maximumFractionDigits: 4 })} tCO2e</Field>
          <Field label="Raw Value">{record.value} {record.unit}</Field>
          <Field label="Normalized Unit">{record.normalized_unit}</Field>
          <Field label="Emission Factor">{record.emission_factor}</Field>
          <Field label="Locked Status">{record.locked ? '🔒 Locked' : 'Unlocked'}</Field>
          <Field label="Created At">{record.created_at ? new Date(record.created_at).toLocaleString() : '—'}</Field>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['issues', 'audits', 'raw'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="btn"
            style={{
              background: tab === t ? '#111827' : '#fff',
              color: tab === t ? '#fff' : '#4b5563',
              border: tab === t ? '1px solid #111827' : '1px solid #e5e7eb',
              textTransform: 'capitalize',
              fontSize: '0.8rem',
              padding: '8px 16px',
            }}
          >
            {t === 'issues' && `Validation Issues (${issues.length})`}
            {t === 'audits' && `Audit History (${audits.length})`}
            {t === 'raw' && 'Raw Source Payload'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* 2. Validation Issues */}
        {tab === 'issues' && (
          <div className="table-wrapper" style={{ border: 'none', margin: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Issue Type</th>
                  <th>Message</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {issues.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>No validation issues found.</td>
                  </tr>
                ) : (
                  issues.map(iss => (
                    <tr key={iss.id}>
                      <td><Badge value={iss.severity} styles={SEVERITY_STYLES} /></td>
                      <td>{iss.issue_type}</td>
                      <td style={{ color: '#374151' }}>{iss.message}</td>
                      <td>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: iss.resolved ? '#15803d' : '#b45309', background: iss.resolved ? '#dcfce7' : '#fef3c7', padding: '2px 8px', borderRadius: 12 }}>
                          {iss.resolved ? 'Resolved' : 'Unresolved'}
                        </span>
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>{iss.created_at?.slice(0, 10)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* 3. Audit History */}
        {tab === 'audits' && (
          <div className="table-wrapper" style={{ border: 'none', margin: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Changed By</th>
                  <th>Details</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {audits.length === 0 ? (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>No audit history found.</td>
                  </tr>
                ) : (
                  audits.map(aud => (
                    <tr key={aud.id}>
                      <td>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#4338ca', background: '#e0e7ff', padding: '2px 8px', borderRadius: 12 }}>
                          {aud.action_type}
                        </span>
                      </td>
                      <td>{aud.changed_by_username || 'System'}</td>
                      <td>
                        {aud.new_value?.reason && (
                          <div style={{ fontSize: '0.8rem', color: '#4b5563', marginBottom: 4 }}>
                            <strong>Reason:</strong> {aud.new_value.reason}
                          </div>
                        )}
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace' }}>
                          Old: {JSON.stringify(aud.old_value)} <br />
                          New: {JSON.stringify(aud.new_value)}
                        </div>
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>{aud.timestamp ? new Date(aud.timestamp).toLocaleString() : '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* 4. Raw Source Payload */}
        {tab === 'raw' && (
          <div style={{ padding: 24, background: '#f8fafc' }}>
            <pre style={{ 
              margin: 0, 
              padding: 16, 
              background: '#1e293b', 
              color: '#e2e8f0', 
              borderRadius: 8, 
              fontSize: '0.85rem', 
              overflowX: 'auto',
              fontFamily: 'monospace'
            }}>
              {JSON.stringify(
                record.raw_payload || { 
                  info: "Raw source payload is not directly linked via the API for this record.",
                  notice: "To view raw JSON data, ensure the backend serializer includes the 'raw_payload' field."
                }, 
                null, 
                2
              )}
            </pre>
          </div>
        )}
      </div>
    </Layout>
  )
}


