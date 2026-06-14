import React from 'react'

export default function Pagination({ page, totalPages, total, limit, onPageChange }) {
  const start = ((page - 1) * limit) + 1
  const end = Math.min(page * limit, total)

  const pageButtons = () => {
    const btns = []
    const range = 2
    for (let p = 1; p <= totalPages; p++) {
      if (p === 1 || p === totalPages || (p >= page - range && p <= page + range)) {
        btns.push(p)
      } else if (btns[btns.length - 1] !== '…') {
        btns.push('…')
      }
    }
    return btns
  }

  if (total === 0) return null

  return (
    <div className="pagination">
      <span>
        Showing {start}–{end} of {total.toLocaleString()}
      </span>
      <div className="pagination-controls">
        <button className="page-btn" disabled={page === 1} onClick={() => onPageChange(1)}>«</button>
        <button className="page-btn" disabled={page === 1} onClick={() => onPageChange(page - 1)}>‹</button>
        {pageButtons().map((p, i) =>
          p === '…'
            ? <span key={`ellipsis-${i}`} style={{ color: 'var(--text-3)', padding: '0 4px' }}>…</span>
            : <button key={p} className={`page-btn${p === page ? ' active' : ''}`} onClick={() => onPageChange(p)}>{p}</button>
        )}
        <button className="page-btn" disabled={page === totalPages} onClick={() => onPageChange(page + 1)}>›</button>
        <button className="page-btn" disabled={page === totalPages} onClick={() => onPageChange(totalPages)}>»</button>
      </div>
    </div>
  )
}
