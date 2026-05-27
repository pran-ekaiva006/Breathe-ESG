import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { getEmissions, getValidationIssues } from '../api/client'

function StatCard({ label, value }) {
  return (
    <div className="card">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value ?? '—'}</p>
    </div>
  )
}

export default function Dashboard() {
  const [emissionData, setEmissionData] = useState(null)
  const [issueData, setIssueData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getEmissions({ page_size: 1 }),
      getEmissions({ approval_status: 'pending', page_size: 1 }),
      getValidationIssues({ resolved: false, page_size: 1 }),
    ]).then(([all, pending, issues]) => {
      setEmissionData({ total: all.count, pending: pending.count })
      setIssueData({ open: issues.count })
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  return (
    <Layout title="Dashboard">
      <div className="grid-stats">
        <StatCard label="Total Emission Records" value={loading ? '…' : emissionData?.total} />
        <StatCard label="Pending Approval"        value={loading ? '…' : emissionData?.pending} />
        <StatCard label="Open Validation Issues"  value={loading ? '…' : issueData?.open} />
      </div>

      <div className="card">
        <p className="text-sm font-semibold" style={{ color: '#374151', marginBottom: 12 }}>Quick Actions</p>
        <div className="flex gap-3">
          <a href="/uploads" className="btn btn-primary">Upload Data</a>
          <a href="/reviews" className="btn btn-secondary">Review Records</a>
        </div>
      </div>
    </Layout>
  )
}
