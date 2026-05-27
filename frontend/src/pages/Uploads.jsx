import { useState } from 'react'
import Layout from '../components/Layout'
import { uploadSAP, uploadUtility, uploadTravel } from '../api/client'

const SOURCES = ['SAP', 'UTILITY', 'TRAVEL']
const UPLOAD_FNS = { SAP: uploadSAP, UTILITY: uploadUtility, TRAVEL: uploadTravel }

export default function Uploads() {
  const [source, setSource] = useState('SAP')
  const [datasourceId, setDatasourceId] = useState('')
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !datasourceId) return
    setLoading(true)
    setResult(null)
    setError(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('datasource_id', datasourceId)
    try {
      const data = await UPLOAD_FNS[source](fd)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.error ?? 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout title="Uploads">
      <div className="max-w-lg">
        <div className="card mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Upload CSV Data</h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source Type</label>
              <select className="select" value={source} onChange={e => setSource(e.target.value)}>
                {SOURCES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">DataSource ID</label>
              <input
                className="input"
                type="number"
                placeholder="e.g. 1"
                value={datasourceId}
                onChange={e => setDatasourceId(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">CSV File</label>
              <input
                className="input"
                type="file"
                accept=".csv"
                onChange={e => setFile(e.target.files[0])}
                required
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Uploading…' : 'Upload'}
            </button>
          </form>
        </div>

        {error && (
          <div className="card border-red-200 bg-red-50 text-red-700 text-sm">{error}</div>
        )}

        {result && (
          <div className="card">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Upload Summary</p>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-gray-500">Status</dt>
              <dd className="font-medium">{result.upload_status}</dd>
              <dt className="text-gray-500">Rows Processed</dt>
              <dd className="font-medium text-green-700">{result.rows_processed}</dd>
              <dt className="text-gray-500">Rows Failed</dt>
              <dd className="font-medium text-red-700">{result.rows_failed}</dd>
              <dt className="text-gray-500">Job ID</dt>
              <dd className="font-medium">#{result.upload_job_id}</dd>
            </dl>
          </div>
        )}
      </div>
    </Layout>
  )
}
