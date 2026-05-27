import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { Table, Pagination } from '../components/Table'
import { StatusBadge, SourceBadge, SeverityBadge } from '../components/Badge'
import { getEmissions } from '../api/client'

const COLUMNS = [
  { key: 'id',               label: '#' },
  { key: 'organization_name', label: 'Organization' },
  { key: 'source_type',      label: 'Source',   render: v => <SourceBadge value={v} /> },
  { key: 'scope_category',   label: 'Scope' },
  { key: 'activity_type',    label: 'Activity' },
  { key: 'co2e_value',       label: 'tCO2e',   render: v => Number(v).toFixed(3) },
  { key: 'record_date',      label: 'Date' },
  { key: 'approval_status',  label: 'Status',  render: v => <StatusBadge value={v} /> },
]

export default function Reviews() {
  const navigate = useNavigate()
  const [data, setData]       = useState({ count: 0, results: [] })
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)
  const [sourceType,  setSourceType]  = useState('')
  const [status,      setStatus]      = useState('')
  const [severity,    setSeverity]    = useState('')

  const load = (p = 1) => {
    setLoading(true)
    const params = { page: p }
    if (sourceType) params.source_type = sourceType
    if (status)     params.approval_status = status
    if (severity)   params.validation_severity = severity
    getEmissions(params)
      .then(d => { setData(d); setPage(p) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [sourceType, status, severity])

  return (
    <Layout title="Reviews">
      <div className="flex-filters">
        <select className="select w-40" value={sourceType} onChange={e => setSourceType(e.target.value)}>
          <option value="">All Sources</option>
          <option>SAP</option><option>UTILITY</option><option>TRAVEL</option>
        </select>
        <select className="select w-44" value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select className="select w-44" value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">Any Severity</option>
          <option value="high">High Issues</option>
          <option value="medium">Medium Issues</option>
          <option value="low">Low Issues</option>
        </select>
      </div>

      <p className="text-sm text-gray-500 mb-3">{data.count} record{data.count !== 1 ? 's' : ''}</p>

      <Table
        columns={COLUMNS}
        rows={data.results}
        loading={loading}
        onRowClick={row => navigate(`/records/${row.id}`)}
      />
      <Pagination page={page} count={data.count} onPageChange={p => load(p)} />
    </Layout>
  )
}
