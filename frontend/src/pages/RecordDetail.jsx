import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { Table } from '../components/Table'
import { StatusBadge, SourceBadge, SeverityBadge } from '../components/Badge'
import { getEmission, getEmissionIssues, getEmissionAudits } from '../api/client'

function Field({ label, children }) {
  return (
    <div>
      <p style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>{label}</p>
      <p style={{ fontSize: '0.875rem', color: '#111827', margin: 0 }}>{children ?? '—'}</p>
    </div>
  )
}

const ISSUE_COLS = [
  { key: 'issue_type', label: 'Type' },
  { key: 'severity',   label: 'Severity', render: v => <SeverityBadge value={v} /> },
  { key: 'message',    label: 'Message' },
  { key: 'resolved',   label: 'Resolved', render: v => v ? '✓' : '✗' },
  { key: 'created_at', label: 'Created',  render: v => v?.slice(0, 10) },
]

const AUDIT_COLS = [
  { key: 'action_type',        label: 'Action' },
  { key: 'changed_by_username', label: 'By' },
  { key: 'timestamp',          label: 'When', render: v => v?.slice(0, 19).replace('T', ' ') },
]

export default function RecordDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [record, setRecord]   = useState(null)
  const [issues, setIssues]   = useState([])
  const [audits, setAudits]   = useState([])
  const [tab, setTab]         = useState('issues')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getEmission(id),
      getEmissionIssues(id),
      getEmissionAudits(id),
    ]).then(([rec, iss, aud]) => {
      setRecord(rec)
      setIssues(iss.results ?? [])
      setAudits(aud.results ?? [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  if (loading) return <Layout title="Record Detail"><p className="text-sm text-gray-500">Loading…</p></Layout>
  if (!record) return <Layout title="Record Detail"><p className="text-sm text-red-500">Record not found.</p></Layout>

  return (
    <Layout title={`Record #${record.id}`}>
      <button onClick={() => navigate(-1)} className="btn btn-secondary mb-5" style={{ fontSize: '0.8rem' }}>
        ← Back
      </button>

      <div className="card mb-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <SourceBadge value={record.source_type} />
            <span className="text-xs text-gray-500">{record.scope_category}</span>
          </div>
          <StatusBadge value={record.approval_status} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }}>
          <Field label="Organization">{record.organization_name}</Field>
          <Field label="Activity">{record.activity_type}</Field>
          <Field label="Record Date">{record.record_date}</Field>
          <Field label="tCO2e">{Number(record.co2e_value).toFixed(4)}</Field>
          <Field label="Value">{record.value} {record.unit}</Field>
          <Field label="Normalized Unit">{record.normalized_unit}</Field>
          <Field label="Emission Factor">{record.emission_factor}</Field>
          <Field label="Locked">{record.locked ? 'Yes' : 'No'}</Field>
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        {['issues', 'audits'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="btn"
            style={{
              background: tab === t ? '#111827' : '#fff',
              color: tab === t ? '#fff' : '#374151',
              border: tab === t ? '1px solid #111827' : '1px solid #d1d5db',
              textTransform: 'capitalize',
              fontSize: '0.8rem',
            }}
          >
            {t === 'issues' ? `Validation Issues (${issues.length})` : `Audit History (${audits.length})`}
          </button>
        ))}
      </div>

      {tab === 'issues' && <Table columns={ISSUE_COLS} rows={issues} />}
      {tab === 'audits' && <Table columns={AUDIT_COLS} rows={audits} />}
    </Layout>
  )
}
