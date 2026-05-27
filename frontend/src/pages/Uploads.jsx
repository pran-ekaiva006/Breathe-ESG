import { useState } from 'react'
import Layout from '../components/Layout'
import { uploadSAP, uploadUtility, uploadTravel } from '../api/client'

const UPLOAD_SECTIONS = [
  {
    key: 'SAP',
    title: 'SAP Data Upload',
    description: 'Upload fuel consumption and operational data exported from SAP. Expected columns: plant_code, fuel_type, quantity, unit, transaction_date.',
    uploadFn: uploadSAP,
    endpoint: 'POST /api/uploads/sap/',
  },
  {
    key: 'UTILITY',
    title: 'Utility Data Upload',
    description: 'Upload electricity billing data from utility providers. Expected columns: meter_id, billing_start, billing_end, usage_kwh, tariff.',
    uploadFn: uploadUtility,
    endpoint: 'POST /api/uploads/utility/',
  },
  {
    key: 'TRAVEL',
    title: 'Travel Data Upload',
    description: 'Upload business travel records for Scope 3 emissions. Expected columns: traveler_name, transport_type, departure_airport, arrival_airport, distance_km, trip_date.',
    uploadFn: uploadTravel,
    endpoint: 'POST /api/uploads/travel/',
  },
]

function UploadCard({ section }) {
  const [file, setFile] = useState(null)
  const [datasourceId, setDatasourceId] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file || !datasourceId) return
    setLoading(true)
    setResult(null)
    setError(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('datasource_id', datasourceId)
    try {
      const data = await section.uploadFn(fd)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.error ?? 'Upload failed. Please check your file and try again.')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setDatasourceId('')
  }

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div className="flex items-center" style={{ gap: 10, marginBottom: 6 }}>
          <span className="badge badge-gray" style={{ fontSize: '0.65rem', letterSpacing: '0.05em' }}>
            {section.key}
          </span>
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: '#111827' }}>
            {section.title}
          </h3>
        </div>
        <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280', lineHeight: 1.5 }}>
          {section.description}
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleUpload}>
        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr auto', gap: 12, alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
              DataSource ID
            </label>
            <input
              className="input"
              type="number"
              min="1"
              placeholder="e.g. 1"
              value={datasourceId}
              onChange={e => setDatasourceId(e.target.value)}
              required
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
              CSV File
            </label>
            <input
              className="input"
              type="file"
              accept=".csv"
              onChange={e => setFile(e.target.files[0])}
              required
              style={{ padding: '6px 12px' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ whiteSpace: 'nowrap' }}>
            {loading ? 'Uploading…' : 'Upload'}
          </button>
        </div>
      </form>

      {/* Loading state */}
      {loading && (
        <div style={{ marginTop: 16, padding: '12px 16px', borderRadius: 8, background: '#f3f4f6', fontSize: '0.8rem', color: '#6b7280' }}>
          ⏳ Processing your file…
        </div>
      )}

      {/* Error state */}
      {error && (
        <div style={{ marginTop: 16, padding: '12px 16px', borderRadius: 8, background: '#fef2f2', border: '1px solid #fecaca', fontSize: '0.8rem', color: '#dc2626' }}>
          ✗ {error}
          <button onClick={resetForm} className="btn btn-secondary" style={{ marginLeft: 12, fontSize: '0.75rem', padding: '4px 10px' }}>
            Reset
          </button>
        </div>
      )}

      {/* Success state */}
      {result && (
        <div style={{ marginTop: 16, padding: '16px', borderRadius: 8, background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
          <p style={{ margin: '0 0 8px', fontSize: '0.8rem', fontWeight: 600, color: '#15803d' }}>
            ✓ Upload complete
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            <div>
              <p className="stat-label">Job ID</p>
              <p style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#111827' }}>#{result.upload_job_id}</p>
            </div>
            <div>
              <p className="stat-label">Status</p>
              <p style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#111827' }}>{result.upload_status}</p>
            </div>
            <div>
              <p className="stat-label">Rows OK</p>
              <p style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#15803d' }}>{result.rows_processed}</p>
            </div>
            <div>
              <p className="stat-label">Rows Failed</p>
              <p style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: result.rows_failed > 0 ? '#dc2626' : '#111827' }}>{result.rows_failed}</p>
            </div>
          </div>
          <button onClick={resetForm} className="btn btn-secondary" style={{ marginTop: 12, fontSize: '0.75rem', padding: '4px 10px' }}>
            Upload Another
          </button>
        </div>
      )}
    </div>
  )
}

export default function Uploads() {
  return (
    <Layout title="Uploads">
      <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: 24 }}>
        Upload CSV files from SAP, utility providers, or travel systems to ingest ESG source data.
      </p>
      {UPLOAD_SECTIONS.map(section => (
        <UploadCard key={section.key} section={section} />
      ))}
    </Layout>
  )
}
