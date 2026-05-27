/* Reusable data table */
export function Table({ columns, rows, onRowClick, loading }) {
  if (loading) {
    return (
      <div className="table-wrapper">
        <div className="flex items-center justify-center py-16 text-gray-400 text-sm">
          Loading…
        </div>
      </div>
    )
  }

  if (!rows?.length) {
    return (
      <div className="table-wrapper">
        <div className="flex items-center justify-center py-16 text-gray-400 text-sm">
          No records found.
        </div>
      </div>
    )
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.id ?? i}
              onClick={() => onRowClick?.(row)}
              className={onRowClick ? 'cursor-pointer' : ''}
            >
              {columns.map(col => (
                <td key={col.key}>
                  {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* Pagination bar */
export function Pagination({ page, count, pageSize = 25, onPageChange }) {
  const total = Math.ceil(count / pageSize)
  if (total <= 1) return null
  return (
    <div className="pagination">
      <button
        className="page-btn"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
      >
        ← Prev
      </button>
      <span className="px-3 py-1.5 text-sm text-gray-500">
        {page} / {total}
      </span>
      <button
        className="page-btn"
        disabled={page === total}
        onClick={() => onPageChange(page + 1)}
      >
        Next →
      </button>
    </div>
  )
}
