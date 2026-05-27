import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { getEmissions, getValidationIssues } from '../api/client'

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

export default function Reviews() {
  const navigate = useNavigate()
  const [data, setData]       = useState({ count: 0, results: [] })
  const [issues, setIssues]   = useState([])
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)

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

    // Fetch validation issues as required
    getValidationIssues()
      .then(d => setIssues(d.results || []))
      .catch(() => setIssues([]))
  }

  useEffect(() => { load(1) }, [sourceType, status])

  const toggleExpand = (e, id) => {
    e.stopPropagation()
    setExpandedId(expandedId === id ? null : id)
  }

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
              <th style={{ width: 40 }}></th>
              <th>Source</th>
              <th>Scope</th>
              <th>Activity</th>
              <th style={{ textAlign: 'right' }}>Value</th>
              <th>Unit</th>
              <th>Status</th>
              <th>Issues</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>
                  Loading…
                </td>
              </tr>
            ) : data.results.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>
                  No records found. Adjust your filters or upload data first.
                </td>
              </tr>
            ) : (
              data.results.map(row => {
                const rowIssues = issues.filter(i => i.emission_record_id === row.id)
                const hasIssues = rowIssues.length > 0
                const highestSeverity = hasIssues
                  ? (rowIssues.some(i => i.severity === 'high') ? 'high' : rowIssues.some(i => i.severity === 'medium') ? 'medium' : 'low')
                  : null

                return (
                  <React.Fragment key={row.id}>
                    <tr
                      onClick={() => navigate(`/records/${row.id}`)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td onClick={(e) => hasIssues && toggleExpand(e, row.id)}>
                        {hasIssues && (
                          <span style={{ cursor: 'pointer', color: '#6b7280', fontSize: '0.8rem' }}>
                            {expandedId === row.id ? '▼' : '▶'}
                          </span>
                        )}
                      </td>
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
                      <td>
                        {hasIssues ? (
                          <Badge value={highestSeverity} styles={SEVERITY_STYLES} />
                        ) : (
                          <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>None</span>
                        )}
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>{row.created_at?.slice(0, 10)}</td>
                    </tr>
                    {expandedId === row.id && hasIssues && (
                      <tr style={{ background: '#f8fafc' }}>
                        <td colSpan={9} style={{ padding: '16px 32px' }}>
                          <h4 style={{ margin: '0 0 12px 0', fontSize: '0.85rem', color: '#475569', fontWeight: 600 }}>Validation Issues</h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {rowIssues.map(issue => (
                              <div key={issue.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px', background: '#fff', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                                <Badge value={issue.severity} styles={SEVERITY_STYLES} />
                                <span style={{ flex: 1, fontSize: '0.85rem', color: '#334155' }}>{issue.message}</span>
                                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: issue.resolved ? '#15803d' : '#b45309', background: issue.resolved ? '#dcfce7' : '#fef3c7', padding: '2px 8px', borderRadius: 12 }}>
                                  {issue.resolved ? 'Resolved' : 'Unresolved'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                )
              })
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

