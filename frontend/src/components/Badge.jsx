const SEVERITY_CLASS = { high: 'badge-red', medium: 'badge-yellow', low: 'badge-gray' }
const STATUS_CLASS = { approved: 'badge-green', pending: 'badge-yellow', rejected: 'badge-red' }

export function SeverityBadge({ value }) {
  return <span className={SEVERITY_CLASS[value] ?? 'badge-gray'}>{value}</span>
}

export function StatusBadge({ value }) {
  return <span className={STATUS_CLASS[value] ?? 'badge-gray'}>{value}</span>
}

export function SourceBadge({ value }) {
  return <span className="badge-gray">{value}</span>
}
