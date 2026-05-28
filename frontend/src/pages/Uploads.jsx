import { useState } from 'react'
import Layout from '../components/Layout'
import { uploadSAP, uploadUtility, uploadTravel, normalizeSAP, normalizeUtility, normalizeTravel } from '../api/client'

const SOURCE_OPTIONS = [
  { value: 'SAP', label: 'SAP Fuel / Procurement', id: 2, uploadFn: uploadSAP, normalizeFn: normalizeSAP },
  { value: 'UTILITY', label: 'Utility Electricity', id: 1, uploadFn: uploadUtility, normalizeFn: normalizeUtility },
  { value: 'TRAVEL', label: 'Corporate Travel', id: 3, uploadFn: uploadTravel, normalizeFn: normalizeTravel },
]

export default function Uploads() {
  const [sourceType, setSourceType] = useState('SAP')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file || !sourceType) return

    setLoading(true)
    setResult(null)
    setError(null)

    const config = SOURCE_OPTIONS.find(opt => opt.value === sourceType)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('datasource_id', config.id)

    try {
      const data = await config.uploadFn(fd)
      if (data.upload_status === 'completed' || data.rows_processed > 0) {
        // Automatically normalize valid records
        const normData = await config.normalizeFn(data.upload_job_id)
        setResult({ ...data, ...normData })
      } else {
        setResult(data)
      }
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
    // Resetting file input value visually requires a bit of DOM interaction, 
    // but React state will handle the logic.
    document.getElementById('csv-file-input').value = ''
  }

  return (
    <Layout title="Upload Data Source">
      <p style={{ fontSize: '0.9rem', color: '#6b7280', marginBottom: 24 }}>
        Select a source type and upload a CSV file for ingestion.
      </p>

      <div className="card" style={{ maxWidth: 500 }}>
        <form onSubmit={handleUpload}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#4b5563', marginBottom: 6 }}>
              Source Type
            </label>
            <select
              className="select"
              value={sourceType}
              onChange={e => setSourceType(e.target.value)}
              style={{ width: '100%', padding: '8px 12px' }}
            >
              {SOURCE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#4b5563', marginBottom: 6 }}>
              CSV File
            </label>
            <input
              id="csv-file-input"
              className="input"
              type="file"
              accept=".csv"
              onChange={e => setFile(e.target.files[0])}
              required
              style={{ width: '100%', padding: '8px 12px' }}
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading} 
            style={{ width: '100%', padding: '10px', display: 'flex', justifyContent: 'center' }}
          >
            {loading ? 'Processing...' : 'Upload & Process'}
          </button>
        </form>

        {/* Error state */}
        {error && (
          <div style={{ marginTop: 20, padding: '12px 16px', borderRadius: 8, background: '#fef2f2', border: '1px solid #fecaca', fontSize: '0.85rem', color: '#dc2626' }}>
            ✗ {error}
          </div>
        )}

        {/* Success state */}
        {result && (
          <div style={{ marginTop: 20, padding: '16px', borderRadius: 8, background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
            <p style={{ margin: '0 0 12px', fontSize: '0.9rem', fontWeight: 600, color: '#15803d' }}>
              ✓ Upload complete
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <div>
                <p className="stat-label">Job ID</p>
                <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#111827' }}>#{result.upload_job_id}</p>
              </div>
              <div>
                <p className="stat-label">Status</p>
                <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#111827' }}>{result.upload_status}</p>
              </div>
              <div>
                <p className="stat-label">Rows OK</p>
                <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#15803d' }}>{result.rows_processed}</p>
              </div>
              <div>
                <p className="stat-label">Rows Failed</p>
                <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: result.rows_failed > 0 ? '#dc2626' : '#111827' }}>{result.rows_failed}</p>
              </div>
            </div>
            <button onClick={resetForm} className="btn btn-secondary" style={{ marginTop: 16, width: '100%', display: 'flex', justifyContent: 'center' }}>
              Upload Another
            </button>
          </div>
        )}
      </div>
    </Layout>
  )
}
