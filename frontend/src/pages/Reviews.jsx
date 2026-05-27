import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { getEmissions } from '../api/client'

const PAGE_SIZE = 20

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

function Badge({ value, styles }) {
  const s = styles[value] || { background: '#f3f4f6', color: '#4b5563' }
  return (
    <span className="badge" style={s}>{value}</span>
  )
}

export default function Reviews() {
  const navigate = useNavigate()
  const [data, setData]       = useState({ count: 0, results: [] })
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)

  // Filters
  const [sourceType, setSourceType] = useState('')
  const [status, setStatus]         = useState('')

  const totalPages = Math.ceil(data.count / PAGE_SIZE)

  const load = (p = 1) => {
    setLoading(true)
    const params = { page: p, page_size: PAGE_SIZE }
    if (sourceType) params.source_type = sourceType
    if (status)     params.approval_status = status
    getEmissions(params)
      .then(d => { setData(d); setPage(p) })
      .catch(() => setData({ count: 0, results: [] }))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [sourceType, status])

  return (
    <Layout title="Reviews">
      {/* Filters */}
      <div className="flex-filters">
        <select className="select w-40" value={sourceType} onChange={e => setSourceType(e.target.value)}>
          <option value="">All Sources</option>
          <option value="SAP">SAP</option>
          <option value="UTILITY">Utility</option>
          <option value="TRAVEL">Travel</option>
        </select>
        <select className="select w-44" value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <span style={{ fontSize: '0.8rem', color: '#9ca3af', alignSelf: 'center' }}>
          {data.count} record{data.count !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Scope</th>
              <th>Activity</th>
              <th style={{ textAlign: 'right' }}>Value</th>
              <th>Unit</th>
              <th>Status</th>
              <th>Locked</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>
                  Loading…
                </td>
              </tr>
            ) : data.results.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>
                  No records found. Adjust your filters or upload data first.
                </td>
              </tr>
            ) : (
              data.results.map(row => (
                <tr
                  key={row.id}
                  onClick={() => navigate(`/records/${row.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td><Badge value={row.source_type} styles={SOURCE_STYLES} /></td>
                  <td>{row.scope_category}</td>
                  <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row.activity_type}
                  </td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {Number(row.value).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td>{row.unit}</td>
                  <td><Badge value={row.approval_status} styles={STATUS_STYLES} /></td>
                  <td>{row.locked ? '🔒' : '—'}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>{row.created_at?.slice(0, 10)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination" style={{ justifyContent: 'center', marginTop: 20 }}>
          <button
            className="page-btn"
            disabled={page <= 1}
            onClick={() => load(page - 1)}
          >
            ← Prev
          </button>
          {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
            let p
            if (totalPages <= 7) {
              p = i + 1
            } else if (page <= 4) {
              p = i + 1
            } else if (page >= totalPages - 3) {
              p = totalPages - 6 + i
            } else {
              p = page - 3 + i
            }
            return (
              <button
                key={p}
                className={`page-btn${p === page ? ' active' : ''}`}
                onClick={() => load(p)}
              >
                {p}
              </button>
            )
          })}
          <button
            className="page-btn"
            disabled={page >= totalPages}
            onClick={() => load(page + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </Layout>
  )
}
